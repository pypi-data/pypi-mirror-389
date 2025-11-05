import math
from . import *

C_MAIN = std_core(20, 8, 
                 ["LED", "SDAT", "SCTL",
                  "FCI0", "FCI1",
                  "MUH", "MUL", "RND",
                  "TTL", "GPIO", "ATRG",
                  "ECTR", "CTRX"],
                  {"GPIO": ["DIR", "INV", "POS", "NEG", "TRG"],
                   "CTRX": [f"C{i:X}" for i in range(32)]},
                 131072, 131072)

def CORE_RWG():
    regs = ["LED", "SDAT", "SCTL", "FCI0", "FCI1",
            "MUH", "MUL", "RND", "TTL", "GPIO", 
            "ECTR", "CTRX", "CMON", "CDDS", "CSBG",
            "MSBG", "DLAY"]
    for w in ["F", "P", "A"]:
        for s in range(64):
            regs += [f"{w}{s:02X}"]
    msbg = []
    for d in range(4):
        msbg += [f"MX{d}L", f"MX{d}H"]
    msbg += [f"SCA{i}" for i in range(4)] + ["OFSC"]
    sub = {"GPIO": ["DIR", "INV", "POS", "NEG", "TRG"],
           "CTRX": [f"C{i:X}" for i in range(4)],
           "CMON": [f"D{i:X}" for i in range(4)],
           "MSBG": msbg}
    return std_core(20, 0, regs, sub, 131072, 131072)

C_RWG = CORE_RWG()

A0 = (0, 0, 0, 0)
A1 = (1, 1, 1, 1)

@multi(asm)
def init(ofsc=19):
    """
    
    Reset & initialize the registers & peripherals.

    Returns
    -------
    None.

    """
    timer()
    ldi('led',0)
    for s in range(64):
        mov(f'F{s:02X}','nul',B=0)
        mov(f'P{s:02X}','nul',B=0)
        mov(f'A{s:02X}','nul',B=0)
    sbg.signal()
    sbg.ctrl(sfq=A1, cph=A1, sam=A1, pud=A1)
    signal(prof=A0)
    ctrl(rst=A1)
    delay(0, 0, 90, 57)
    sel('msbg','ofsc')
    ldi('msbg',ofsc,B=0)
    for chn in range(4):
        regwrite(chn, 0x1, [0x01, 0x01, 0x00, 0x20])
        regwrite(chn, 0x2, [0x00, 0x00, 0xC0, 0x00])
        regwrite(chn, 0x3, [0x00, 0x00, 0x00, 0xFF])
        regwrite(chn, 0xA, [0x18, 0x00, 0x00, 0x00])
        ducwrite(chn, 0, 2, 1, 0, 0, 0, 0)
        regwrite(chn, 0x0, [0x00, 0x60, 0x20, 0x02])
        sbg.mux(chn, 0xFFFF << (chn*16), 0)

@multi(asm)
def sync():
    """
    
    Synchronize the datalink between DDS and FPGA.

    Returns
    -------
    None.

    """
    timer(150)
    sbg.signal()
    sbg.ctrl(pud=(1, 1, 1, 1))
    timer(150)
    ctrl(synrst=1)

@multi(asm)
def spi_send(slv_adr, dst_reg, adr_len, dat_len, clk_div, ltn=0, wait=True):
    val = bit_concat((clk_div, 8), (dat_len, 4), (adr_len, 1),
                     (slv_adr, 3), (ltn, 4), (dst_reg, 12))
    ldi('sctl', val)
    if wait:
        sleep((clk_div + 1) * (16 * (dat_len + adr_len + 2)))
         
_prof = [0] * 4
    
@multi(asm)
def signal(iou=A0, mrk=A0, prof=(None,None,None,None),load=True):
    global _prof
    p = [0] * 4
    tmp = [0] * 4
    for i in range(4):
        p[i] = _prof[i] if prof[i] is None else prof[i]
        tmp[i] = bit_concat((iou[i], 1), (mrk[i], 1),
                            (p[i], 3))
    _prof = p
    val = bit_concat((0, 12),
                        (tmp[3], 5), (tmp[2], 5),
                        (tmp[1], 5), (tmp[0], 5))
    if load:
        ldl('cdds',val)
    else:
        return val

@multi(asm)
def ctrl(rst=A0, iorst=A0, synrst=0, load=True):
    tmp = [0] * 4
    for i in range(4):
        tmp[i] = bit_concat((rst[i], 1), (iorst[i], 1))
    val = bit_concat((0, 3), (synrst, 1),
                        (tmp[3], 2), (tmp[2], 2),
                        (tmp[1], 2), (tmp[0], 2), 
                        (0, 20))
    if load:
        ldh('cdds',val)
    else:
        return val

@multi(asm)
def delay(prof=0, mrk_sgt=0, mrk_sbg=90, iou_sbg=57):
    val = bit_concat((prof, 8), (mrk_sgt, 8), (mrk_sbg, 8), (iou_sbg, 8))
    ldi('dlay',val)

def sig_msk(chn, val=1, oth=0):
    ret = [oth] * 4
    ret[chn] = val
    return ret

RegLen = [4, 4, 4, 4, 4, 6, 6, 4,
            2, 4, 4, 8, 8, 4, 8, 8,
            8, 8, 8, 8, 8, 8, 4, 0, 2, 2]
CDiv_DDSW = 1
CDiv_DDSR = 5
LTN_DDSR = 1

@multi(asm)
def regwrite(chn, reg, dat, clk=None, wait=True, ioupd=True):
    tln = len(dat)
    dat = dat + ([0] * (-tln % 4))
    ln = len(dat) // 4
    ins = [0] * ln
    for i in range(ln):
        ins[i] = bit_concat((dat[i*4], 8), (dat[i*4+1], 8),
                            (dat[i*4+2], 8), (dat[i*4+3], 8))
    for i in range(ln):
        ldi('sdat',ins[ln-i-1],B=1)
    spi_send(chn+1, reg, 0, tln, clk or CDiv_DDSW, ltn=0, wait=wait)
    if ioupd:
        signal(iou=sig_msk(chn))

@multi(asm)
def profwrite(chn, prof, frq, amp, pha, wait=True, ioupd=True):
    ftw = round((frq / 1200) * (2 ** 32))
    ftw = ftw.to_bytes(4, "big")
    asf = round(amp * 16383).to_bytes(2, "big")
    phw = round(pha * 65536).to_bytes(2, "big")
    regwrite(chn, prof + 14, list(asf + phw + ftw), wait=wait, ioupd=ioupd)

@multi(asm)
def ducwrite(chn, prof, ccir, s_inv, i_cci, frq, amp, pha, wait=True, ioupd=True):
    ctr = bit_concat((ccir, 6), (s_inv, 1), (i_cci, 1)).to_bytes(1, "big")
    ftw = round((frq / 1200) * (2 ** 32)).to_bytes(4, "big")
    asf = round(amp * 255).to_bytes(1, "big")
    phw = round(pha * 65536).to_bytes(2, "big")
    regwrite(chn, prof + 14, list(ctr + asf + phw + ftw), wait=wait, ioupd=ioupd)

@multi(asm)
def carrier(chn, frq, amp=1.0, pha=0.0, upd=False):
    ducwrite(chn, 0, 2, 1, 0, frq, amp, pha, wait=True, ioupd=upd)

@multi(asm)
def wait_master():
    timer()
    smk('err','!nul','0x1.0',B=0)
    nop(4)

@multi(asm)
def trig_slave(slave, offset=476):
    """
    
    Trigger the selected slave boards. Used in pair with <Wait_Master>.

    Parameters
    ----------
    slave : <list>
        List of addresses of the selected slave boards.
    offset : <int> or <float>, optional
        Delay after sending the trigger. Use it to align the behavior
        of the main board with the slave boards.
        
        <int>: the duration is in unit of cycles (3.33ns).
        
        <float>: the duration is in unit of micro-second.
        
        The default is 476. With this value, the GPIO output is aligned with
        MARK output of the RWG boards with RTLink baud-rate = 2.

    Returns
    -------
    None.

    """
    bce = sum([1 << (i-1) for i in slave])
    if isinstance(offset, float):
        offset = round(offset * 300)
    timer(offset)
    set_rtcf(hop=0, typ=1, bce=bce, bcs=0)
    nop(2)
    with asm:
        ins = smk('err','nul','0x1.0')
    ldi('rtbc',ins)
    set_rtcf(typ=0)
    
@multi(asm)
def cfg_gpio(dir=None, inv=None, pos=None, neg=None, trg=None):
    """
    
    Configurations of GPIO ports. Set the direction, inversion, sensitivity
    of each port and whether a port is used as trigger. The parameters are 
    32-bit integers with each bit corresponds to a port. The power-up defaults
    are 0.
    
    inv, pos, neg and trg take effect only for input ports. The input level
    is first optionally inverted, then the sensitive edges are converted to
    pulses, and finally used for triggering and counting.
    
    If neither pos nor neg is asserted for a port,
    the port is high-level sensitive.
    
    If more than one ports are used as trigger, any one can fire the trigger.
    
    Parameters
    ----------
    dir : <int>, optional
        Direction of the GPIO ports, 1 for input, 0 for output.
    inv : <int>, optional
        Logic invert flag, 1 for invert.
    pos : <int>, optional
        Positive-edge sensitive flag, 1 for sensitive.
    neg : <int>, optional
        Negative-edge sensitive flag, 1 for sensitive.
    trg : <int>, optional
        Trigger enable flag, 1 for used as trigger.

    Returns
    -------
    None.

    """
    if dir is not None:
        sel('gpio','dir')
        mov('gpio',dir)
    if inv is not None:
        sel('gpio','inv')
        mov('gpio',inv)
    if pos is not None:
        sel('gpio','pos')
        mov('gpio',pos)
    if neg is not None:
        sel('gpio','neg')
        mov('gpio',neg)
    if trg is not None:
        sel('gpio','trg')
        mov('gpio',trg)
        
def _get_scale(val, wid):
    orig = val
    tmp = max(-val - 1 if val < 0 else val, 1)
    scl = max(round(math.log2(tmp)) + 2 - wid, 0)
    val = val >> scl
    if scl >= 16 or (orig != 0 and val == 0) or not (-2048 <= val < 2048):
        raise
    return val, scl

def _adr_sb(idx):
    return (None if len(idx) < 2 else idx[0]),idx[-1]     

class SBG(meta):
    @staticmethod                        
    def signal(txe=A0, mrk=A0):
        tmp = [0] * 4
        for i in range(4):
            tmp[i] = bit_concat((0, 1), (txe[i], 1), (mrk[i], 1))
        val = bit_concat((tmp[3], 3), (tmp[2], 3),
                         (tmp[1], 3), (tmp[0], 3), (0, 20))
        ldh('csbg',val)

    @staticmethod
    def ctrl(iou=A0, sfq=A0, cph=A0, sam=A0, pud=A0):
        tmp = [0] * 4
        for i in range(4):
            tmp[i] = bit_concat((iou[i], 1), (sfq[i], 1), (cph[i], 1),
                                (sam[i], 1), (pud[i], 1))
        val = bit_concat((0, 12),
                         (tmp[3], 5), (tmp[2], 5),
                         (tmp[1], 5), (tmp[0], 5))
        ldl('csbg',val)
    
    @staticmethod
    def play(dur, phase_origin=False, txe=A1, mrk=A0, sfq=A0, sam=A0, strict=True):
        """
        
        Apply the SBG parameter changes and start generating waves.

        Parameters
        ----------
        dur : <int> or <float>
            Duration of this PlayWave stage.

            <int>: the duration is in unit of cycles (3.33ns).
            
            <float>: the duration is in unit of micro-second.
            
        phase_origin : <tuple> or <bool>, optional
            Whether to clear phase accumulators of the carrier and sidebands.
            Should be 2-tuple of 4-tuples, e.g. ((0, 0, 0, 0), (1, 1, 1, 1)),
              with the first tuple corresponding to the carrier.
            True is the same as ((1, 1, 1, 1), (1, 1, 1, 1));
              False is the same as ((0, 0, 0, 0), (0, 0, 0, 0)).
            The default is False.
        txe : tuple of 4, optional
            Parallel modulation enable flag of each RF port, aligned with RF waveform output.
            The default is (1, 1, 1, 1).
        mrk : tuple of 4, optional
            Output state of each GPIO port, aligned with RF waveform output.
            The default is (0, 0, 0, 0).
        sfq : tuple of 4, optional
            Frequency update flag of each RF port.
            1 for clear frequency ramp accumulator and set new sideband frequency.
            Affect all SBGs assigned to the corresponding RF channel.
            The default is (0, 0, 0, 0).
        sam : tuple of 4, optional
            Amplitude update flag of each RF port.
            1 for clear amplitude ramp accumulator and set new sideband amplitude.
            Affect all SBGs assigned to the corresponding RF channel.
            The default is (0, 0, 0, 0).

        Returns
        -------
        None.

        """
        if phase_origin is True:
            car = A1
            cph = A1
        elif phase_origin is False:
            car = A0
            cph = A0
        else:
            car, cph = phase_origin
        if type(dur) is float:
            dur = round(dur * 300)
        if type(dur) is int:
            dur = dur & -2
        if type(mrk) is int:
            mrk = bit_split(mrk,(1,1,1,1))
        timer(dur,strict=strict)
        sbg.signal(txe=A1, mrk=mrk)
        sbg.ctrl(iou=car, sfq=sfq, cph=cph, sam=sam, pud=A1)
        
    @staticmethod
    def mux(chn, ena=None, scale=None):
        """
        
        Configure the association of SBGs to the RF channels.

        Parameters
        ----------
        chn : <int>, 0-3
            The RF channel number to be configured.
        ena : <int>
            64 bit integer, each bit corresponds to a SBG. 1 for associating this SBG to the RF channel.
        scale : <int>
            SBG signal attenuation level for this RF channel.
            The signals of the SBGs associated to a channel are first summed 
            then shifted right <scale> bits before output to dds.
        
        NOTE: By default, SBG 0-15 are with RF channel 0, 16-31 with channel 1, etc. And scale is 0.

        Returns
        -------
        None.

        """
        if ena is not None:
            sel('msbg', f"MX{chn}L")
            ldi('msbg', ena)
            sel('msbg', f"MX{chn}H")
            ldi('msbg', ena >> 32)
        if scale is not None:
            sel('msbg', f"SCA{chn}")
            ldi('msbg', scale)

    @staticmethod
    def ftw(sb,frq,high_res=True):
        '''
        frq : <float>, -60.0 - +60.0
        Sideband frequency offset in MHz.
        '''
        ftw = round((frq / 150.0) * 0x1_0000_0000)
        ftw_crs = (ftw >> 12) & 0xFFFFF
        ftw_fin = ftw & 0xFFF
        ftw = bit_concat((ftw_fin, 12), (ftw_crs, 20))
        if sb is None:
            return ftw
        r_f = f"F{sb:02X}"
        ldl(r_f,ftw,B=0)
        if high_res:
            ldh(r_f,ftw,B=0)

    @staticmethod 
    def asf(sb,am_p,am_n=0,high_res=True):
        '''
        am_p : <float>, 0.0 - 1.0
            Positive sideband amplitude.
        am_n : <float>, 0.0 - 1.0
            Negative sideband amplitude. NOTE: abs(am_p ± am_n) <= 1
        '''
        asp = round(am_p * 0x7FFF)
        asp_crs = (asp >> 6) & 0x3FF
        asp_fin = asp & 0x3F
        asn = round(am_n * 0x7FFF)
        asn_crs = (asn >> 6) & 0x3FF
        asn_fin = asn & 0x3F
        asf = bit_concat((asn_fin, 6), (asp_fin, 6), 
                         (asn_crs, 10), (asp_crs, 10))
        if sb is None:
            return asf
        r_a = f"A{sb:02X}"
        ldl(r_a,asf,B=0)
        if high_res:
            ldh(r_a,asf,B=0)

    @staticmethod
    def pof(sb,pha,org=0,high_res=True):
        '''
        pha : <float>, 0.0 - 1.0
        Sideband phase offset, in unit of 2PI.
        '''
        pof = round(pha * 0x1_00000 + (org >> 13)) & 0xFFFFF
        if sb is None:
            return pof
        r_p = f"P{sb:02X}"
        ldl(r_p,pof,B=0)
        if high_res:
            ldh(r_p,0,B=0)    

    @staticmethod
    def ramp(sb,fsi=None,ar_p=None,ar_n=None):
        '''
        fsi : <float>, signed, 1e-5 - 350.0, optional
        Frequency ramp rate, in unit of MHz/us.
        Setting to None disables frequency ramp.
        ar_p : <float>, signed, 0.005 - 18.0, optional
            Positive sideband amplitude ramp rate, in unit of 1/us.
        ar_n : <float>, signed, 0.005 - 18.0, optional
            Negative sideband amplitude ramp rate, in unit of 1/us.
            Setting ar_p or ar_n to None disables amplitude ramp.
        '''
        if fsi is not None:
            fsi = round((fsi / 22500.0) * 0x1_0000_0000)
            fsi, fsf = _get_scale(fsi, 12)
            fsi <<= 20
            fse = 1
        else:
            fsf, fse = 0, 0
        if ar_p is not None or ar_n is not None:
            if ar_p is None:
                ar_p = 0
            if ar_n is None:
                ar_n = 0
            arp = round(ar_p * 0x7FFF / 150.0)
            arn = round(ar_n * 0x7FFF / 150.0)
            arp, afp = _get_scale(arp, 6)
            arn, afn = _get_scale(arn, 6)
            arx = bit_concat((arn, 6), (arp, 6)) << 20
            are = 1
        else:
            arx = None
            afp, afn, are = 0, 0, 0
        scn = bit_concat((fse, 1), (are, 1), (fsf, 4), (afn, 3), (afp, 3)) << 20
        if sb is None:
            return fsi,arx,scn
        r_f = f"F{sb:02X}"
        r_p = f"P{sb:02X}"
        r_a = f"A{sb:02X}"
        if fsi is not None:
            ldh(r_f,fsi,B=0)
        if arx is not None:
            ldh(r_a,arx,B=0)
        ldh(r_p,scn,B=0)       
    
    def f(self,frq,high_res=True):
        adr,sb = _adr_sb(self.__meta__)
        self.ftw[adr](sb,frq,high_res)
        return self
    
    def a(self,am_p,am_n=0,high_res=True):
        adr,sb = _adr_sb(self.__meta__)
        self.asf[adr](sb,am_p,am_n,high_res)
        return self
     
    def p(self,pha,org=0,high_res=True):
        adr,sb = _adr_sb(self.__meta__)
        self.pof[adr](sb,pha,org,high_res)
        return self
    
    def r(self,fsi=None,ar_p=None,ar_n=0):
        adr,sb = _adr_sb(self.__meta__)
        self.ramp[adr](sb,fsi,ar_p,ar_n)
        return self

SBG.ctrl = multi(asm,SBG.ctrl)
SBG.signal = multi(asm,SBG.signal)
SBG.play = multi(asm,SBG.play)
SBG.mux = multi(asm,SBG.mux)
SBG.ftw = multi(asm,SBG.ftw)
SBG.asf = multi(asm,SBG.asf)
SBG.pof = multi(asm,SBG.pof)
SBG.ramp = multi(asm,SBG.ramp)

sbg = SBG()

@multi(asm)
def ttl_level(ttl):
    mov('ttl',ttl,B=0)

@multi(asm)
def ttl_stage(dur,ttl):
    if type(dur) is float:
        dur = round(dur * 300)
    if type(dur) is int:
        dur = dur & -2
    timer(dur)
    ttl_level(ttl)
    
@multi(asm)
def save_count(ctr, ext=False):
    """
    
    Save the counts of the selected counters to data cache.
    The counts can only be accessed after deactivation.

    Parameters
    ----------
    ctr : <int>
        32-bit integer, each bit corresponds to a counter.
        1 for selecting this channel.

    Returns
    -------
    None.

    """
    sleep(120)
    ldi('dca',0)
    nop(4)
    mov('dca','dcd')
    for i in range(3 if ext else 4):
        if ctr & (1 << i) > 0:
            sel('ctrx',f"C{i:X}")
            add('dca','dca',1,B=0)
            mov('dcd','ctrx',B=0)
            nop(2)
    if ext and (ctr & 0b1000 > 0):
        sleep(24000)
        for i in range(4, 36):
            sel('ctrx',f"C{i:X}")
            add('dca','dca',1,B=0)
            mov('dcd','ctrx',B=0)
            nop(2)
    nop(2)
    mov('tr0','dca',B=0)
    ldi('dca',0,B=0)
    nop(2)
    mov('dcd','tr0')
    
if __name__ == '__main__':
    with asm as f:
        asm.multi=[1, 2, 3]
        setup(C_RWG)
        #init()
        #sbg.ftw(0x00,10)
        #sbg.asf[1](0x00,0.5)
        #sbg.pof[2,3](0x00,0)
        sbg[0x00].f(10).a(0.5)
        sbg[1,2][0x00].p(0)
        finish()
    print(f['1'][:],f['2'][:],f['3'][:])