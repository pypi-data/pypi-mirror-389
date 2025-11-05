import os,sys
PYODIDE = 'pyodide' in sys.modules
if PYODIDE:
    import js,pyodide
try:
    import veri
    veri.lib = os.path.join(os.path.dirname(os.path.realpath(__file__)),'..','..','..','hdl','rwg',sys.platform)
except:
    pass
try:    
    import serial
except:
    pass
try:
    import ftd3xx
except:
    pass
from . import asm,base_core,reach_node,suspend_node,node_exec,reset_node,resume_node,download_to,unpack_frame

class base_intf:
    def __init__(self):
        self.open_cnt = 0
        self.oper = {}
    
    def open(self):
        if self.open_cnt == 0:
            self.open_device()
        self.open_cnt += 1
    
    def close(self):
        self.open_cnt -= 1
        if self.open_cnt == 0:
            self.close_device()

    def __enter__(self):
        self.open()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open_device(self):
        raise NotImplementedError()

    def close_device(self):
        raise NotImplementedError()

    def set_timeout(self, tout):
        raise NotImplementedError()

    def write(self, frm):
        raise NotImplementedError()

    def read(self):
        raise NotImplementedError()

    def alloc_read_buffer(self, cnt):
        raise NotImplementedError()
    
    def baud_reset(self):
        raise NotImplementedError()

    def reset(self):
        import time
        enter = self.open_cnt > 0
        while self.open_cnt > 0:
            self.__exit__(0, 0, 0)
        with self:
            cycleDevicePort = getattr(self.dev,'cycleDevicePort',None)
            if cycleDevicePort:
                cycleDevicePort()
        time.sleep(0.8)
        with self:
            self.baud_reset()
        time.sleep(0.05)
        if enter:
            self.__enter__()
            
    def run(self, dnld, prg, adr=0, cnt=0, tout=5, ssp=True):
        if type(prg) in (bytes,bytearray):
            buf = prg
        else:
            buf = reach_node(adr, ssp)
            if dnld & 1 == 0:
                if dnld & 2 == 0:
                    buf += suspend_node(adr)
                buf += node_exec(adr, prg)
                if not dnld & 4:
                    buf += resume_node(adr)
            else:
                buf += reset_node(adr)
                download = getattr(self,'download',None)
                if download:
                    download(adr, prg)
                else:
                    buf += download_to(adr, prg)
                buf += resume_node(adr)
            buf = bytes(buf)
        self.set_timeout(tout)
        if cnt > 0:
            self.alloc_read_buffer(cnt)
        elif cnt < 0:
            self.alloc_read_buffer(1)
        self.write(buf)
        if cnt > 0:
            return self.read()
        elif cnt == 0:
            return
        fin = True
        while True:
            try:
                pld = self.read()
            except TimeoutError:
                continue
            if fin:
                pld = pld[0]
                narg,oper = pld>>20,pld&0xfffff
                if oper == 0:
                    if narg == 0:
                        break
                else:
                    oper = self.oper[oper]
                self.set_timeout(tout)
                self.alloc_read_buffer(narg or 1)
                fin = False
            elif narg == 0:
                fin = oper(pld)
                self.set_timeout(tout)
                self.alloc_read_buffer(1)
            else:
                if oper == 0:
                    return pld
                else:
                    oper(*pld)
                    self.set_timeout(tout)
                    self.alloc_read_buffer(1)
                    fin = True

class ft601_intf(base_intf):
    def __init__(self, sn):
        self.sn = sn
        self.tout = 5.0
        super().__init__()
    
    def open_device(self):
        sn = bytes(self.sn, encoding="utf-8")
        self.dev = ftd3xx.create(sn, ftd3xx.FT_OPEN_BY_SERIAL_NUMBER)
        if self.dev is None:
            raise RuntimeError(f"Incorrect serial number: {self.sn}")

    def close_device(self):
        if self.dev is not None:
            self.dev.close()
        self.dev = None

    def set_timeout(self, tout):
        self.tout = tout
        self.dev.setPipeTimeout(0x02, int(tout * 1000))
        self.dev.setPipeTimeout(0x82, int(tout * 1000))

    def write(self, frm):
        self._write(self._frm_to_raw(frm))

    def read(self):
        dat = self._raw_to_frm(self._get_async_read())
        if len(dat) < 5*self.read_cnt:
            self.dev.abortPipe(0x02)
            self.dev.abortPipe(0x82)
            self.dev.resetDevicePort()
        payloads = []
        for i in range(self.read_cnt):
            frm = dat[5*i:5*(i+1)]
            if len(frm) < 5:
                raise RuntimeError(f"Data receive timed out, {len(payloads)} frames received.")
            pld, hdr = unpack_frame(frm)
            if hdr[0] == base_core.MGW_ERR:
                raise RuntimeError("Runtime error occured in RTMQ core.")
            elif hdr[0] != base_core.MGW:
                raise RuntimeError(f"Corrupted frame header: {hdr}.")
            elif hdr[2] == 0:
                payloads += [pld]
            else:
                return payloads
        return payloads

    def alloc_read_buffer(self, cnt):
        self._init_async_read(cnt * 8)
        self.read_cnt = cnt

    def baud_reset(self):
        self._write(b"\x00" * 8)

    def _write(self, dat):
        return self.dev.writePipe(0x02, dat, len(dat))

    def _sync_read(self, ln):
        return self.dev.readPipeEx(0x82, ln)[1]

    def _init_async_read(self, ln):
        self.ovlp = self.dev.initOverlapped()
        self.rd_dat = self.dev.asyncReadPipe(0x82, ln, self.ovlp)

    def _get_async_read(self):
        byt = self.dev.getOverlappedResult(self.ovlp)
        if self.dev.getLastError() != 0:
            print(f"getovlp: {ftd3xx.getStrError(self.dev.getLastError())}")
            self.dev.abortPipe(0x82)
            self.dev.resetDevicePort()
        self.dev.releaseOverlapped(self.ovlp)
        return self.rd_dat.raw[:byt]

    def _frm_to_raw(self, f):
        cnt = len(f) // 5
        tmp = [f[i*5:i*5+1]+b"\x00"*3+f[i*5+4:i*5:-1] for i in range(cnt)]
        return b"".join(tmp)
    
    def _raw_to_frm(self, r):
        cnt = len(r) // 8
        tmp = [r[i*8:i*8+1]+r[i*8+7:i*8+3:-1] for i in range(cnt)]
        return b"".join(tmp)

class uart_intf(base_intf):
    def __init__(self, port, baud):
        self.port = port
        self.baud = baud
        super().__init__()

    def open_device(self):
        self.dev = serial.Serial(self.port, self.baud)
        self.dev.reset_input_buffer()
        self.dev.reset_output_buffer()
        self.dev.stopbits = serial.STOPBITS_ONE

    def close_device(self):
        if self.dev is not None:
            self.dev.close()
        self.dev = None

    def set_timeout(self, tout):
        self.dev.timeout = tout
        self.dev.write_timeout = tout

    def write(self, frm):
        self.dev.write(frm)
    
    def read(self):
        payloads = []
        for i in range(self.read_cnt):
            frm = self.dev.read(5)
            if len(frm) < 5:
                raise RuntimeError(f"Data receive timed out, {len(payloads)} frames received.")
            pld, hdr = unpack_frame(frm)
            if hdr[0] == base_core.MGW_ERR:
                raise RuntimeError("Runtime error occured in RTMQ core.")
            elif hdr[0] != base_core.MGW:
                raise RuntimeError(f"Corrupted frame header: {hdr}.")
            elif hdr[2] == 0:
                payloads += [pld]
            else:
                return payloads
        return payloads

    def alloc_read_buffer(self, cnt):
        self.read_cnt = cnt

    def baud_reset(self):
        self.dev.write(b"\x00" * 5)

class sim_intf(base_intf):
    def __init__(self, top='top', io=None, trace=0):
        self.top = top.lower() if type(top) is str else top
        self.io = io or ((['FP_LED_MAIN']+[f'FP_LED_RWG{i+1}' for i in range(3)]) if self.top == 'top' else ['FP_LED_RWG1'])
        self.trace = trace
        super().__init__()
        
    def open_device(self):
        if callable(self.top):
            self.dev = self.top()
        else:
            if PYODIDE:
                import json
                js.eval(f'veri.${self.top}=veri.top("rwg.{self.top}",{json.dumps(self.io)},{self.trace})')
                self.dev = getattr(js.veri,f'${self.top}')
                self.dev.run()
            else:
                self.dev = veri.top(self.top,self.io,self.trace)
                self.dev.run()

    def close_device(self):
        if self.dev is not None:
            self.dev.close()
        self.dev = None

    def set_timeout(self, tout):
        self.tout = tout
        
    def write(self, frm):
        self.dev.write(frm)
    
    def read(self):
        payloads = []
        for i in range(self.read_cnt):
            frm = self.dev.read(5, self.tout)
            if PYODIDE:
                frm = frm.to_py()
            if len(frm) < 5:
                raise RuntimeError(f"Data receive timed out, {len(payloads)} frames received.")
            pld, hdr = unpack_frame(frm)
            if hdr[0] == base_core.MGW_ERR:
                raise RuntimeError("Runtime error occured in RTMQ core.")
            elif hdr[0] != base_core.MGW:
                raise RuntimeError(f"Corrupted frame header: {hdr}.")
            elif hdr[2] == 0:
                payloads += [pld]
            else:
                return payloads
        return payloads

    def alloc_read_buffer(self, cnt):
        self.read_cnt = cnt

    def baud_reset(self):
        self.dev.write(b'\x00' * 5)
    
    def download(self,addr,prg):
        dev = self.dev       
        if addr == 0:
            ich = dev.rwg__DOT__iRWG1__DOT__ICCH__DOT__MEM__BRA__0__KET____DOT__mem
            if ich is None:
                ich = dev.top__DOT__iMAIN__DOT__ICCH__DOT__MEM__BRA__0__KET____DOT__mem
        else:
            rwg = getattr(dev,f'__PVT__top__DOT__iRWG{addr}')
            ich = getattr(rwg,'__PVT__ICCH__DOT__MEM__BRA__0__KET____DOT__mem')
        for i in range(len(prg)):
            ich[i] = prg[i]

#intf = sim_intf('RWG')
#intf = ft601_intf('IONCxHYQ4')
#intf = uart_intf('COM3',2000000)
