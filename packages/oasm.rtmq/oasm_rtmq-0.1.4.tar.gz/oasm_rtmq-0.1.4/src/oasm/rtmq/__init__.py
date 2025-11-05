import pkgutil
__path__ = pkgutil.extend_path(__path__,__name__)
__path__.reverse()

from contextlib import contextmanager
from .. import *

def bit_concat(*args):
    """

    Bit fields concatenation.

    Parameters
    ----------
    *args : 2-tuples as (V, W)
        Each argument corresponds to a bit field with value V and width W.
        Bit fields are concatenated from high to low.
        NOTE: V will be cropped if not less than (2 ** W)

    Returns
    -------
    dat : integer
        Concatenated value.

    Example
    -------
    bit_concat((0b11, 2), (0b10, 3), (0b11, 1)) == 0b110101

    """
    dat = 0
    ln = len(args)
    for i in range(ln - 1):
        dat |= args[i][0] & ((1 << args[i][1]) - 1)
        dat <<= args[i + 1][1]
    dat |= args[ln - 1][0] & ((1 << args[ln - 1][1]) - 1)
    return dat

def bit_split(dat, wids):
    """

    Split a number into bit fields.

    Parameters
    ----------
    dat : integer
        Number to be splitted.
    wids : list OR tuple of integers
        Width of each bit field.

    Returns
    -------
    bf : list of integers
        Values of bit fields.

    Example
    -------
    bit_split(0b110101, (2, 3, 1)) == [0b11, 0b10, 0b1]

    """
    bf = []
    for i in range(1, len(wids)):
        bf += [dat & ((1<<wids[-i])-1)]
        dat = dat >> wids[-i]
    bf += [dat & ((1<<wids[0])-1)]
    bf.reverse()
    return bf
    
class base_core:
    """

    Base class for RTMQ core structure,
    defines constants and registers common to the RTMQ framework.

    Constants
    ----------
    OPC   : Type-A instruction opcodes.
    MGW   : Magic word of RTLink frame.
    RSV   : Reserved registers (core registers & system peripherals).
    T_ERR : Error message.

    Attributes
    ----------
    REG     : List of register names.
    SBF     : Dict of register sub-file entries.
    CAP_ICH : Maximum capacity of instruction cache.
    CAP_DCH : Maximum capacity of data cache.

    """
    OPC = {"ADD": "AA", "AND": "LL", "XOR": "LL",
           "CLU": "AA", "CLS": "AA", "CEQ": "LA",
           "SGN": "AA", "SNE": "LA", "SMK": "LL", "MOV": "RR",
           "SLL": "LA", "SLA": "LA", "SLC": "LA"}
    MGW = 0xA
    MGW_ERR = 0x5
    RSV = ["NUL", "PTR", "WCK", "TIM", "TRG", "ERR",
           "ICA", "ICD", "DCA", "DCD", "RTS", "DTS",
           "RTCF", "RTBC", "RTDA"]
    T_ERR = ["Core suspended",
             "ALU register write conflict",
             "Timeout exceeded",
             "Trigger misaligned"]

    def __init__(self, regs, sbfs, cap_ich, cap_dch):
        """

        Parameters
        ----------
        regs : list of strings
            List of all other registers.
        sbfs : dict of lists of strings
            The key of each item is the entry register name, 
            and the value is a list of names of the registers in the sub-file.
        cap_ich : integer
            Maximum capacity of instruction cache.
        cap_dch : integer
            Maximum capacity of data cache.

        Returns
        -------
        None.

        """
        self.REG = self.RSV + regs
        self.alu_opc = dict()
        opc = list(self.OPC.keys())
        for i in range(len(opc)):
            self.alu_opc[opc[i]] = i
        self.regs = dict()
        for i in range(len(self.REG)):
            self.regs[self.REG[i]] = i
        self.SBF = sbfs
        self.sbfs = dict()
        for k, v in self.SBF.items():
            self.sbfs[k] = dict()
            for i in range(len(v)):
                self.sbfs[k][v[i]] = i
        self.CAP_ICH = cap_ich
        self.CAP_DCH = cap_dch

class std_core(base_core):
    """

    Standard RTMQ core structure
    with basic computation and flow control capability.

    Constants
    ----------
    RSV_GPR : Assembler reserved general purpose registers. \n
    N_PLM   : Cache pipeline latency. \n
    N_PLI   : Type-I instruction pipeline latency. \n
    N_PLA   : Type-A instruction pipeline latency. \n
    N_PLS   : Stack pop pipeline latency. \n
    T_ERR   : Error message.


    """

    RSV_GPR = ["TR0", "TR1", "NOW"]

    N_PLM = 3
    N_PLI = 1
    N_PLA = 4
    N_PLS = 4

    T_ERR = ["PTR out of bound",
             "ICA out of bound",
             "DCA out of bound",
             "RTS overflow",
             "RTS underflow",
             "DTS overflow",
             "DTS underflow",
             "RTLink Rx FIFO overflow",
             "RTLink ExtUART Tx conflict",
             "Error occured in slave nodes"]

    def __init__(self, n_gpr, n_slv, regs, sbfs, cap_ich, cap_dch):
        """

        Parameters
        ----------
        n_gpr : integer
            Number of non-reserved general-purpose registers.
        n_slv : integer
            Number of RTLink slaves (within 0-15).
        regs : list of strings
            List of all other registers.
        sbfs : dict of lists of strings
            The key of each item is the entry register name, 
            and the value is a list of names of the registers in the sub-file.
        cap_ich : integer
            Maximum capacity of instruction cache.
        cap_dch : integer
            Maximum capacity of data cache.

        Returns
        -------
        None.

        """
        self.n_gpr = n_gpr
        treg = self.RSV_GPR.copy()
        for i in range(n_gpr):
            treg += [f"R{i:X}"]
        treg += regs
        tsbf = {"RTDA": []}
        for i in range(n_slv + 1):
            tsbf["RTDA"] += [f"C{i:X}"]
        for k, v in sbfs.items():
            tsbf[k] = v
        super().__init__(treg, tsbf, cap_ich, cap_dch)
        self.T_ERR = super().T_ERR + self.T_ERR

# Global instance used to implement basic operations
C_BASE = base_core([], {"RTDA": ["C0"]}, 65536, 16384)
C_STD = std_core(20, 0, [], {}, 65536, 16384)

def source(code, core=None, line=True):
    """

    Convert machine code program back to assembly program.

    Parameters
    ----------
    code : list of integers
        Program in machine code.
    core : <CoreBase>, optional
        Destination core structure descriptor. The default is None.

    Returns
    -------
    prg : multi-line string
        Assembly program.

    """
    if core is None:
        core = getattr(code,'core',asm.core)
    if type(code) is int:
        ith, itl, h, f, opc, rd, i0, i1, n0, n1, rx = \
            bit_split(code, (1, 1, 1, 1, 4, 8, 1, 1, 1, 1, 12))
        cod = ("LDH", "LDL")[itl] if ith == 0 else list(core.OPC.keys())[opc]
        if cod == "LDH":
            if rd == 0:
                cod = "NOP"
            elif opc >= 0x8:
                cod = "SEL"
        hld = ("-", "H")[h]
        fct = ("-", "F")[f]
        head = f"{cod} {hld} {fct}"
        rds = f"{core.REG[rd]:4}"
        if ith == 0:
            imm = bit_concat((opc, 4), (i0, 1), (i1, 1),
                             (n0, 1), (n1, 1), (rx, 12))
            if itl == 0:
                if opc >= 0x8:
                    s = bit_concat((opc, 3), (i0, 1), (i1, 1), (n0, 1), (n1, 1))
                    ims = core.SBF[core.REG[rd]][s]
                else:
                    ims = f"0x{imm:03X}_00000"
            else:
                ims = f"0x000_{imm:05X}"
            if cod == "NOP":
                instr = head
            else:
                instr = f"{head}  {rds}  {ims}"
        else:
            ird = (" ", "!")[itl]
            ir0 = (" ", "!")[n0]
            ir1 = (" ", "!")[n1]
            r0, r1 = (0, rx) if opc == 9 else bit_split(rx, (6, 6))
            r0l = bit_split(bit_concat((n0, 1), (r0, 6)), (3, 4))
            r0l = f" 0x{r0l[1]:X}.{r0l[0]}"
            r0i = f" 0x{r0:02X}" if n0 == 0 else f"-0x{0x40-r0:02X}"
            r0i = {"R": "", "A": r0i, "L": r0l}[core.OPC[cod][0]]
            r0s = f"{ir0}{core.REG[r0]}" if i0 == 0 else r0i
            r1l = bit_split(bit_concat((n1, 1), (r1, 6)), (3, 4))
            r1l = f" 0x{r1l[1]:X}.{r1l[0]}"
            r1i = f" 0x{r1:02X}" if n1 == 0 else f"-0x{0x40-r1:02X}"
            r1i = {"R": "", "A": r1i, "L": r1l}[core.OPC[cod][1]]
            r1s = f"{ir1}{core.REG[r1]}" if i1 == 0 else r1i
            if cod == "MOV":
                instr = f"{head} {ird}{rds} {r1s}"
            else:
                instr = f"{head} {ird}{rds} {r0s} {r1s}"
        return instr
    elif type(code) in (tuple,list,table):
        prg = [source(ins,core) for ins in code]
        if line:
            return '\n'.join([f'{i:05X}:\t{prg[i]}' for i in range(len(prg))])
        else:
            return '\n'.join(prg)
    return str(code)
        
'''
core : <CoreBase>, optional
    Destination core structure descriptor. The default is None.
label : dict, optional
    Dict of jump labels. The default is dict().
'''
asm = context(core=C_STD)

def label(tag,put=True):
    lbl = getattr(asm,'label',None)
    if lbl is None:
        lbl = {}
        asm.label = lbl
    pos = lbl.get(tag,None)
    if put is True or type(put) is int:
        if put is True:
            put = len(asm)
        if type(pos) is list:
            pos[0][0] = put
            for i in pos[1:]:
                asm[i] = asm[i]()
        lbl[tag] = put
    else:
        if type(pos) is int:
            return pos
        if pos is None:
            pos = [expr(put)]
            lbl[tag] = pos
        pos.append(len(asm))
        return pos[0]
        
def cnv_opd(opd, opc, field, typ):
    if type(opd) not in (int,float,str,core_reg):
        if "A" not in typ:
            raise
        return (label(id(opd),opd),1,0)
    opd = str(opd)
    try:
        if opd[0] == '#':
            if "A" not in typ:
                raise
            return (label(opd[1:],None), 1, 0)
        elif opd[0] == '-' or opd[0].isdigit():
            num = opd.split('.')
            if len(num) == 1:
                if "A" not in typ:
                    raise
                return (int(opd, 0) & 0xFFFF_FFFF, 1, 0)
            else:
                nib = int(num[0], 0)
                pos = int(num[1])
                if not ((0 <= nib <= 15) and (0 <= pos <= 7) and ("L" in typ)):
                    raise
                return ((pos << 4) | nib, 1, 0) 
        inv = 0
        while opd[0] == "!":
            opd = opd[1:]
            inv = 1 - inv
        if "R" not in typ:
            raise
        return (asm.core.regs[opd.upper()], 0, inv)
    except:
        raise SyntaxError(f"Invalid {field} for {opc}: '{opd}'.")       

def nop(n=1,H=0,F=0):
    ins = [(H << 29) | (F << 28)] * n
    asm(*ins)
    return ins

def bubble(n,flag=None):
    if flag is None:
        flag = getattr(asm,'bubble',None)
    if flag:
        nop(n)
    
def sel(rd,sbf,H=0,F=0):
    rd = rd.upper()
    RD, tmp, nRD = cnv_opd(rd, 'SEL', 'RD', 'R')
    if rd not in asm.core.SBF.keys():
        raise SyntaxError(f"'{rd}' is not a register sub-file.")
    sbf = sbf.upper()
    if sbf not in asm.core.SBF[rd]:
        raise SyntaxError(f"Invalid register '{sbf}' in sub-file {rd}.")
    RS = asm.core.sbfs[rd][sbf] + 0x80
    ins = (H << 29) | (F << 28) | ((RS >> 4) << 24) | (RD << 16) | ((RS & 0xF) << 12)
    asm(ins)
    return ins

def ldh(rd,imm,H=0,F=0,B=None):
    RD, tmp, nRD = cnv_opd(rd, 'LDH', 'RD', 'R')
    R0, iR0, nR0 = cnv_opd(imm, 'LDH', 'imm', 'A')
    ins = (H << 29) | (F << 28) | (RD << 16) | ((R0 >> 20) & 0xFFFF)
    asm(ins)
    if not (H or F):
        bubble(std_core.N_PLI,B)
    return ins

def ldl(rd,imm,H=0,F=0,B=None):
    RD, tmp, nRD = cnv_opd(rd, 'LDL', 'RD', 'R')
    R0, iR0, nR0 = cnv_opd(imm, 'LDL', 'imm', 'A')
    ins = 0x4000_0000 | (H << 29) | (F << 28) | (((R0 >> 16) & 0xF) << 24) | (RD << 16) | (R0 & 0xFFFF)
    asm(ins)
    if not (H or F):
        bubble(std_core.N_PLI,B)
    return ins

def ldi(rd,imm,H=0,F=0,B=None):
    RD, tmp, nRD = cnv_opd(rd, 'LDH', 'RD', 'R')
    R0, iR0, nR0 = cnv_opd(imm, 'LDH', 'imm', 'A')
    ins = [(H << 29) | (F << 28) | (RD << 16) | ((R0 >> 20) & 0xFFFF),
    0x4000_0000 | (H << 29) | (F << 28) | (((R0 >> 16) & 0xF) << 24) | (RD << 16) | (R0 & 0xFFFF)]
    asm(ins[0])
    R0, iR0, nR0 = cnv_opd(imm, 'LDH', 'imm', 'A')
    asm(ins[1])
    if not (H or F):
        bubble(std_core.N_PLI,B)
    return ins

def is_imm(val):
    if type(val) is str:
        return val[0] in ('#','-') or val[0].isdigit()
    return type(val) is int

def mov(rd,val,H=0,F=0,B=None):
    if callable(val):
        return val(rd,H=H,F=F,B=B)
    else:
        if is_imm(val):
            return ldi(rd,val,H=H,F=F,B=B)
        else:
            RD, tmp, nRD = cnv_opd(rd, 'MOV', 'RD', 'R')
            R1, iR1, nR1 = cnv_opd(val, 'MOV', "R1", "R")
            ins = ((2+nRD)<<30) | (H << 29) | (F << 28) | (asm.core.alu_opc['MOV'] << 24) | (RD << 16) | 0x8000 | (nR1 << 12) | R1
            asm(ins)
            if not (H or F):
                bubble(std_core.N_PLA,B)
            return ins
        
def alu(opc,rd,r0,r1,H=0,F=0,B=None):
    opc = opc.upper()
    if opc not in asm.core.alu_opc.keys():
        raise SyntaxError(f"Invalid opcode: '{opc}'.")
    RD, tmp, nRD = cnv_opd(rd, opc, 'RD', 'R')
    R0, iR0, nR0 = cnv_opd(r0, opc, "R0", "R" + asm.core.OPC[opc][0])
    R1, iR1, nR1 = cnv_opd(r1, opc, "R1", "R" + asm.core.OPC[opc][1])
    if iR0 == 1 and type(R0) is int and (0x000000_7F < R0 < 0xFFFFFF_C0):
        raise ValueError("R0 immediate out of bound.")
    elif iR0 == 0 and R0 > 0x3F:
        raise ValueError("R0 address out of bound.")
    if iR1 == 1 and type(R1) is int and (0x000000_7F < R1 < 0xFFFFFF_C0):
        raise ValueError("R1 immediate out of bound.")
    elif iR1 == 0 and R1 > 0x3F:
        raise ValueError("R1 address out of bound.")
    t0 = (R0 >> 6) & 1 if iR0 else nR0
    t1 = (R1 >> 6) & 1 if iR1 else nR1
    ins = ((2+nRD)<<30) | (H << 29) | (F << 28) | (asm.core.alu_opc[opc]<<24) | (RD<<16) | (((iR0<<3)+(iR1<<2)+(t0<<1)+t1)<<12) | ((R0&0x3F)<<6) | (R1&0x3F)
    asm(ins)
    if not (H or F):
        bubble(std_core.N_PLA,B)
    return ins

for k in base_core.OPC.keys()-['MOV']:
    globals()['and_' if k == 'AND' else k.lower()] = (lambda k:lambda rd,r0,r1,H=0,F=0,B=None:alu(k,rd,r0,r1,H,F,B))(k)

@multi(asm)                
def inline(prg):
    if type(prg) is str:
        prg = prg.splitlines()
    elif type(prg[0]) is int:
        prg = [source(ins) for ins in prg]
    for line in prg:
        instr = line.strip()
        if len(instr) == 0 or instr[0] == '%':
            continue
        if instr[0] == '#' and instr[-1] == ':':
            label(instr[1:-1])
        else:
            instr = instr.split()
            if len(instr) == 1:
                asm(int(instr[0],16))
            else:
                opc = instr[0].lower()
                h = int(instr[1].lower() == 'h') 
                f = int(instr[2].lower() == 'f')
                globals()['and_' if opc == 'and' else opc](*instr[3:],H=h,F=f,B=0)

@multi(asm)
def setup(core=C_STD, dnld=1):
    asm.core = core
    asm.dnld = dnld
    if dnld&1:
        asm.bubble = 1
        mov('trg','trg',B=0)
        timer()

@multi(asm)
def finish():
    dnld = getattr(asm,'dnld',1)
    if dnld&1:
        #rtlk_send(0)
        nop(2,H=1)
    
@multi(asm)
def timer(n=None,strict=True,wait=True):
    if n is None:
        if wait:
            sleep()
        mov('now','wck',B=0)
        mov('trg','trg',B=0)
        smk('err','nul','0x8.0',B=0)
    else:
        if is_imm(n):
            ldi('tr0',n,B=0)
            n = 'tr0'
        if wait:
            sleep()
        mov('now','wck',B=0)
        mov('tim',n,B=0)
        smk('err',('!' if strict else '')+'nul','0x4.0',B=0)

@multi(asm)
def sleep(n=None):
    if n is None:
        mov('nul','err',H=1)
    else:
        cyc = std_core.N_PLA + std_core.N_PLM
        if n <= cyc + 3:
            nop(n)
        else:
            n -= 3
            ldi('tr0',1-n//cyc,B=1)
            sne('ptr','ptr','tr0')
            add('tr0','tr0',1)
            nop(cyc + n % cyc - 2)

def wait_tx(chn_msk):
    nop()
    ldh('tr0',0xFFF00000,B=0)
    ldh('tr1',0xFFF00000,B=0)
    sne('ptr','ptr','tr0',B=0)
    ceq('!tr0','tr1','nul',B=0)
    ldi('tr1',chn_msk)
    and_('tr1','tr1','rtbc',B=0)
    nop(std_core.N_PLM)

@multi(asm)
def rtlk_send(dat, chn=0, wait=True):
    if wait:
        wait_tx(1 << chn)
    sel('rtda',f'C{chn:X}')
    mov('rtda',dat,B=0)

@multi(asm)
def set_rtcf(upl=None, bdr=None, hop=None, typ=None, bce=None, bcs=None):
    upl_msk, upl = (0, 0) if upl is None else (0xF, upl)
    bdr_msk, bdr = (0, 0) if bdr is None else (0xFF, bdr)
    hop_msk, hop = (0, 0) if hop is None else (0x7, hop)
    typ_msk, typ = (0, 0) if typ is None else (0x1, typ)
    bce_msk, bce = (0, 0) if bce is None else (0x7FFF, bce)
    bcs_msk, bcs = (0, 0) if bcs is None else (0x1, bcs)

    val = bit_concat((upl, 4), (bdr, 8), (hop, 3),
                     (typ, 1), (bce, 15), (bcs, 1))
    msk = bit_concat((upl_msk, 4), (bdr_msk, 8), (hop_msk, 3),
                     (typ_msk, 1), (bce_msk, 15), (bcs_msk, 1))
    ldi('tr0',val,B=0)
    ldi('tr1',msk)
    smk('rtcf','tr0','tr1')

@multi(asm)    
def jmp(dst,cond=None,met=True):
    if cond is None:
        if is_imm(dst):
            ldl('ptr',dst,F=1)
        else:
            mov('ptr',dst,F=1)
    else:
        if callable(cond):
            cond('tr1' if met else '!tr1')
            cond = 'tr1'
        elif not met:
            cond = '!'+cond
        if is_imm(dst):
            ldi('tr0',dst)
            dst = 'tr0'
        sne('ptr',dst,cond,F=1)

def block(tag=None,n=0):
    if n > 0:
        blk = table(tag=tag)
        asm.block = getattr(asm,'block',[]) + [blk]
        idx = len(asm.block) - 1
        for i in range(n):
            blk.append(f'{tag}_{idx}_{i}')
        return blk
    if tag is None:
        blk = asm.block.pop()
        if blk.tag == 'for':
            tr0 = blk.step
            if not (-0x40 <= tr0 < 0x40):
                ldi('tr0',tr0)
                tr0 = 'tr0'
            add(blk.rd,blk.rd,tr0,B=0)
        if blk.tag in ('forever','while','for'):
            jmp('#'+blk[0])
        if blk.tag != 'forever':
            blk[-1] = block(blk[-1])
        if blk.tag == 'elif':
            block()
        return blk
    elif type(tag) is str:
        pos = asm.label[tag]
        del asm.label[tag]
        tag = (pos[0],{i:asm[i] for i in pos[1:]})
    tag[0][0] = len(asm)
    for k,v in tag[1].items():
        asm[k] = v()
    return tag
        
@multi(asm)
def if_(cond):
    jmp('#'+block('if',2)[1],cond,False)

@multi(asm)
def elif_(cond):
    else_()
    jmp('#'+block('elif',2)[1],cond,False)

@multi(asm)
def else_():
    blk = asm.block[-1]
    jmp('#'+blk[0])
    block(blk.pop())

@multi(asm)    
def while_(cond=None):
    if cond is None:
        label(block('forever',1)[0])
    else:
        blk = block('while',2)
        label(blk[0])
        jmp('#'+blk[1],cond,False)

@multi(asm)
def for_(rd,rng):
    if type(rng) not in (tuple,list):
        rng = (rng,)
    if len(rng) == 1:
        start = 0
        stop = rng[0]
    else:
        start = rng[0]
        stop = rng[1]
    step = rng[2] if len(rng) > 2 else 1
    tr0 = stop
    if not (-0x40 <= tr0 < 0x40):
        ldi('tr0',tr0)
        tr0 = 'tr0'
    if step > 0:
        cond = lambda tr1,H=0,F=0,B=None:cls(tr1,rd,tr0,H=H,F=F,B=B)
    else:
        cond = lambda tr1,H=0,F=0,B=None:cls(tr1,tr0,rd,H=H,F=F,B=B)
    blk = block('for',2)
    blk.rd = rd
    blk.step = step
    mov(rd,start)
    label(blk[0])
    jmp('#'+blk[1],cond,False)

@multi(asm)    
def end():
    block()

@contextmanager
def If(cond):
    try:
        yield if_(cond)
    except Exception:
        raise
    else:
        asm.last_if = [block()]

@contextmanager
def Elif(cond):
    try:
        asm.block += asm.last_if
        yield elif_(cond)
    except Exception:
        raise
    else:
        asm.last_if.append(block())

@contextmanager
def Else():
    try:
        asm.block += asm.last_if
        yield else_()
    except Exception:
        raise
    else:
        block()
        asm.last_if = []

@contextmanager
def While(cond=None):
    try:
        yield while_(cond)
    except Exception:
        raise
    else:
        block()

@contextmanager
def For(rd, rng):
    try:
        yield for_(rd,rng)
    except Exception:
        raise
    else:
        block()

def frame(*args):
    if len(args) == 0:
        return getattr(asm, 'frame', (0,))
    asm.frame = args
    vars = [R[i] for i in range(sum(args))]
    return vars[0] if len(vars) == 1 else vars

@multi(asm)
def function(name, args=0, locals=0):
    label(name)
    for i in range(locals):
        mov('dts', f'R{(i+args):X}', B=0)
    return frame(args, locals)

@multi(asm)
def return_(*rets):
    for i in range(len(rets)):
        mov(f'R{(asm.core.n_gpr-1-i):X}', rets[i], B=0)
    size = sum(frame())
    for i in range(size):
        mov(f'R{(size-1-i):X}', 'dts')
    mov('ptr','rts',F=1)

@multi(asm)    
def call(name, *args):
    for i in range(len(args)):
        mov('dts', f'R{i:X}', B=0)
        mov(f'R{i:X}', args[i], B=0)
    add('rts','ptr',2,B=0)
    ldl('ptr','#'+name,F=1)
    return R[asm.core.n_gpr-1]

Return = return_
Call = call

@contextmanager
def Func(name, *regs):
    try:
        if len(regs) == 1:
            args = regs[0] + 1
            locals = 0
        else:
            args = regs[0]
            locals = regs[1] + 1 - regs[0]
        yield function(name,args,locals)
    except Exception:
        raise
    else:
        core = asm.core
        with asm:
            asm.core = core
            ins = mov('ptr','rts',F=1)
        if asm[-1] != ins:
            return_()

Set = mov
                    
class core_reg:
    def __init__(self, key=None):
        object.__setattr__(self,'_key',None if key is None else (f'R{key:X}' if type(key) is int else str(key).upper()))
    def __str__(self):
        return 'R' if self._key is None else self._key
    def __getattr__(self, key):
        return self[key]
    def __getitem__(self, key):
        if self._key is None:
            key = f'R{key:X}' if type(key) is int else str(key).upper()
            val = self.__dict__.get(key, None)
            if val is None:
                val = self.__class__(key)
                self.__dict__[key] = val
            return val
    def __setattr__(self, key, val):
        self[key] = val
    def __setitem__(self, key, val):
        if self._key is None:
            key = f'R{key:X}' if type(key) is int else str(key).upper()
            Set(key,val)
    def __eq__(self, other):
        return lambda rd,H=0,F=0,B=None:ceq(rd,self,other,H=H,F=F,B=B)
    def __ne__(self, other):
        return lambda rd,H=0,F=0,B=None:ceq('!'+rd,self,other,H=H,F=F,B=B)
    def __lt__(self, other):
        return lambda rd,H=0,F=0,B=None:cls(rd,self,other,H=H,F=F,B=B)
    def __gt__(self, other):
        return lambda rd,H=0,F=0,B=None:cls(rd,other,self,H=H,F=F,B=B)
    def __le__(self, other):
        return lambda rd,H=0,F=0,B=None:cls('!'+rd,other,self,H=H,F=F,B=B)
    def __ge__(self, other):
        return lambda rd,H=0,F=0,B=None:cls('!'+rd,self,other,H=H,F=F,B=B)
    def __add__(self, other):
        return lambda rd,H=0,F=0,B=None:add(rd,self,other,H=H,F=F,B=B)
    def __sub__(self, other):
        return lambda rd,H=0,F=0,B=None:add(rd,self,(-other) if type(other) is int else ('!'+str(other)),H=H,F=F,B=B)
    def __and__(self, other):
        return lambda rd,H=0,F=0,B=None:and_(rd,self,other,H=H,F=F,B=B)
    def __or__(self, other):
        return lambda rd,H=0,F=0,B=None:and_('!'+rd,'!'+str(self),'!'+str(other),H=H,F=F,B=B)
    def __xor__(self, other):
        return lambda rd,H=0,F=0,B=None:xor(rd,self,other,H=H,F=F,B=B)
    def __lshift__(self, other):
        return lambda rd,H=0,F=0,B=None:sla(rd,self,other,H=H,F=F,B=B)
    def __rshift__(self, other):
        return lambda rd,H=0,F=0,B=None:sla(rd,self,(-other) if type(other) is int else ('!'+str(other)),H=H,F=F,B=B)
    def __radd__(self, other):
        return self.__add__(other)
    def __rsub__(self, other):
        return lambda rd,H=0,F=0,B=None:add(rd,'!'+str(self),other,H=H,F=F,B=B)
    def __rand__(self, other):
        return self.__and__(other)
    def __ror__(self, other):
        return self.__or__(other)
    def __rxor__(self, other):
        return self.__xor__(other)
    def __rlshift__(self, other):
        return lambda rd,H=0,F=0,B=None:sla(rd,other,self,H=H,F=F,B=B)
    def __rrshift__(self, other):
        return lambda rd,H=0,F=0,B=None:sla(rd,other,'!'+str(self),H=H,F=F,B=B)
    def __neg__(self):
        return 0 - self
    def __imatmul__(self, other):
        R[self] = other
        return self
    def __iadd__(self, other):
        R[self] = self + other
        return self
    def __isub__(self, other):
        R[self] = self - other
        return self
    def __iand__(self, other):
        R[self] = self & other
        return self
    def __ior__(self, other):
        R[self] = self | other
        return self
    def __ixor__(self, other):
        R[self] = self ^ other
        return self
    def __ilshift__(self, other):
        R[self] = self << other
        return self
    def __irshift__(self, other):
        R[self] = self >> other
        return self
    
R = core_reg()

core_ctx = lambda core=asm.core:{k:R[k] for k in core.regs}|{k:globals()[k] for k in ('Set','If','Elif','Else','While','For','Return','Call','Func')}
core_regq = lambda core=asm.core:lambda s:s == 'R' or s in core.regs
core_domain = lambda core=asm.core,sub=True,dump=False:domain(core_ctx(core),core_regq(core),sub=sub,dump=dump)

@multi(asm)
def cache_write(adr, dat, typ='d'):
    mov(typ[0]+'ca',adr)
    mov(typ[0]+'cd',dat)

@multi(asm)
def cache_read(adr, typ='d'):
    mov(typ[0]+'ca',adr,B=1)
    nop(std_core.N_PLM)
    return typ[0]+'cd'

class core_cache:
    def __init__(self, typ, ptr=0):
        self.typ = typ
        self.ptr = ptr
    def __setitem__(self, key, val):
        cache_write(key, val, typ=self.typ)
    def __getitem__(self, key):
        return R[cache_read(key, typ=self.typ)]
    def __add__(self, ptr):
        return self.__class__(self.typ, self.ptr + ptr)
    def __call__(self, size):
        ptr = getattr(asm,self.typ,0)
        asm[self.typ] = ptr + size
        return self + ptr

DCH = core_cache('dat')
ICH = core_cache('ins')

def unpack_addr(addr):
    s = hex(addr).lstrip("0x")
    if "0" in s:
        raise RuntimeError(f"Invalid node address: 0x{addr:X}.")
    res = []
    for c in s:
        res += [int(c, 16)]
    return res

def pack_frame(hop, payload, typ=1):
    frm = bit_concat((C_BASE.MGW, 4), (hop, 3), (typ, 1), (payload, 32))
    return frm.to_bytes(5, "big")

def unpack_frame(frm):
    dat = int.from_bytes(frm, "big")
    mgw, hop, typ, pld = bit_split(dat, (4, 3, 1, 32))
    return pld, (mgw, hop, typ)

def send_to(addr, payloads, typ=1):
    """

    Send data / instruction frames to a node.

    Parameters
    ----------
    addr : integer
        Destination node address.
    payloads : list of integers
        Payloads of frames, each element corresponds to a frame.
    typ : integer
        Type of frames.
        0: data frame; 1: instruction frame;
        The default is 1.

    Returns
    -------
    buf : bytearray
        Byte stream of the frames.

    """
    hop = len(unpack_addr(addr))
    ln = len(payloads)
    buf = bytearray(ln * 5)
    head = bit_concat((C_BASE.MGW, 4), (hop, 3), (typ, 1)) << 32
    for i in range(ln):
        buf[i*5:(i+1)*5] = (head | payloads[i]).to_bytes(5, "big")
    return buf

def node_exec(addr, code):
    """

    Run a script on a node using configuration override.

    Parameters
    ----------
    addr : integer
        Destination node address.
    code : int array
        Machine code to be run.

    Returns
    -------
    buf : bytearray
        Byte stream of the script.
        
    """
    return send_to(addr, code, 1)

def suspend_node(addr):
    """

    Generate a script to suspend the destination node.

    Parameters
    ----------
    addr : integer
        Destination node address.

    Returns
    -------
    buf : bytearray
        Byte stream of the script.

    """
    with asm:
        return node_exec(addr,[smk('err','0x1.0','0x1.0')])

def resume_node(addr):
    """

    Generate a script to resume the destination node.

    Parameters
    ----------
    addr : integer
        Destination node address.

    Returns
    -------
    buf : bytearray
        Byte stream of the script.

    """
    with asm:
        return node_exec(addr,[smk('err','0x0.0','0x1.0')])

def reset_node(addr):
    """

    Generate a script to reset the Timer, TrigMgr & ErrorMgr of a node,
    and then jump to address 0.

    Parameters
    ----------
    addr : integer
        Destination node address.

    Returns
    -------
    buf : bytearray
        Byte stream of the script.

    """
    with asm:
        ldl('err',1,F=1)
        mov('trg','trg',H=1)
        mov('tim','nul',H=1)
        mov('ptr','nul',B=0)
        mov('ica','nul',B=0)
        mov('dca','nul',B=0)
        and_('!err','err','nul',B=0)
        return node_exec(addr, asm[:])

def download_to(addr, payloads, typ=1, start=0):
    """

    Generate a script to download data / program to the destination node.

    Parameters
    ----------
    addr : integer
        Destination node address.
    payloads : list of integers
        data / program in machine code.
    core : <CoreBase>, optional
        Destination core structure descriptor. The default is None.
    typ : integer, optional
        Type of payloads.
        0: data (to Data Cache); 1: program (to Instruction Cache);
        The default is 1.
    start : integer, optional
        Start address in the cache. The default is 0.

    Returns
    -------
    buf : bytearray
        Byte stream of the script.

    """
    cap = (asm.core.CAP_DCH, asm.core.CAP_ICH)[typ]
    ln = len(payloads)
    if ln > cap:
        tmp = ("data", "instruction")[typ]
        raise RuntimeError(f"Maximum {tmp} cache capacity exceeded.")
    scr = [0] * (ln * 3 + 1)
    rga = base_core.RSV.index(("DCA", "ICA")[typ])
    rgd = base_core.RSV.index(("DCD", "ICD")[typ])
    scr[0] = rga << 16
    for i in range(ln):
        scr[i*3+1] = 0x40000000 | (((i+start) & 0xF0000) << 8) | (rga << 16) | ((i+start) & 0xFFFF)
        scr[i*3+2] = (rgd << 16) | ((payloads[i] >> 20) & 0xFFF)
        scr[i*3+3] = 0x40000000 | ((payloads[i] & 0xF0000) << 8) | (rgd << 16) | (payloads[i] & 0xFFFF)
    return send_to(addr, scr, 1)

def reach_node(addr, ssp=True):
    """

    Construct a link between the computer and the destination node.
    So that the node can be controlled directly.

    Parameters
    ----------
    addr : integer
        Destination node address.
    ssp : bool, optional
        Whether to suspend the cores in the route. The default is True.

    Returns
    -------
    buf : bytearray
        Byte stream of the script.

    """
    nodes = unpack_addr(addr)
    hop = len(nodes)
    buf = bytearray()
    with asm:
        for i in range(hop):
            t_adr = addr >> ((hop - i) * 4)
            if ssp:
                buf += suspend_node(t_adr)
            rtcf = bit_concat((nodes[i], 4), (0, 12), ((1 << nodes[i]) + 1, 16))
            buf += node_exec(t_adr, ldi('rtcf',rtcf))
        rtcf = bit_concat((0, 12), (hop, 3), (0, 17))
        buf += node_exec(addr, ldi('rtcf',rtcf))
    return buf

class run_cfg:
    def __init__(self, intf, dst, core=None):
        self.intf = intf
        self.dst = dst
        self.core = core
        self.stat = 0

    def __call__(self, *args, **kwargs):
        if self.stat == 0:
            self.func = args[0]
            self.dnld = kwargs["dnld"] if "dnld" in kwargs else 1
            self.rply = kwargs["rply"] if "rply" in kwargs else 1
            self.dst  = kwargs["dst"] if "dst" in kwargs else self.dst
            self.tout = kwargs["tout"] if "tout" in kwargs else 1.0
            self.proc = kwargs["proc"] if "proc" in kwargs else None
            if type(self.func) is not table and callable(self.func):
                self.stat = 1
                return self
        self.stat = 0
        if not callable(self.func):
            flw = self.func
        else:
            with asm as flw:
                asm.intf = self.intf
                asm.tout = self.tout
                asm.proc = self.proc
                if type(self.func) is table:
                    nodes = getattr(self.func,'multi',None)
                    if nodes is None:
                        asm.dnld = self.dnld
                        asm(*self.func[:],**self.func.__dict__)
                    else:
                        asm.multi = nodes
                        for adr in nodes:
                            asm[str(adr)] = self.func[str(adr)].copy()
                            if getattr(asm[str(adr)],'dnld',None) is None:
                                asm[str(adr)].dnld = self.dnld
                else:
                    if self.core is not None:
                        asm.core = self.core
                    asm.dnld = self.dnld
                    res = self.func(*args, **kwargs)
                    if len(asm) == 0:
                        return res
                finish()
        with self.intf:
            res = []
            nodes = getattr(flw,'multi',None)
            if nodes is None:
                rply = getattr(flw,'rply',None)
                if rply is None:
                    rply = getattr(flw,'dnld',None)
                    rply = self.rply if rply is None else (rply&1)
                for adr in self.dst:
                    res += self.intf.run(flw.dnld, flw[:], adr, rply) or []
            else:
                flws = flw
                for i in range(len(self.dst)):
                    flw = flws[str(nodes[i])]
                    res += self.intf.run(flw.dnld, flw[:], self.dst[i], getattr(flw,'rply',(flw.dnld&1) and self.rply))
            proc = getattr(flw,'proc',self.proc)
            if proc is None:
                return None if len(res) == 0 else res
            else:
                return map(proc,res)
        
class assembler:
    def __init__(self, cfg=None, multi=None):
        self.cfg = cfg
        core = cfg and cfg.core or asm.core
        intf = cfg and cfg.intf or asm.intf
        with asm as self.asm:
            if multi is None:
                setup(core)
                asm.intf = intf
            else:
                nodes = []
                cores = []
                for i in multi:
                    if type(i) in (tuple,list):
                        nodes.append(str(i[0]))
                        cores.append(i[1])
                    else:
                        nodes.append(str(i))
                        cores.append(core)
                asm.multi = nodes
                for i in range(len(nodes)):
                    name = nodes[i]
                    setup[name](cores[i])
                    asm[name].intf = intf
                    self[name] = asm < asm[name]
                        
    def __getitem__(self, key):
        return getattr(self, str(key))
    
    def __setitem__(self, key, val):
        return setattr(self, str(key), val)
    
    def run(self, disa=False):
        if disa:
            multi = getattr(self.asm,'multi',None)
            if multi is None:
                print(source(self.asm))
            else:
                for i in multi:
                    print(i)
                    print(source(self.asm[str(i)]))
        if self.cfg and self.cfg.intf:
            return self.cfg(self.asm)
    
    def clear(self):
        multi = getattr(self.asm,'multi',None)
        if multi is None:
            self.asm.clear()
        else:
            for i in multi:
                self.asm[str(i)].clear()
        return self

    def __enter__(self):
        self.asm = asm <= self.asm

    def __exit__(self, exc_type, exc_value, traceback):
        self.asm = asm <= self.asm

    def __call__(self, *args, **kwargs):
        if len(args) > 0:
            multi = getattr(self.asm,'multi',None)
            if multi is None:
                with self:
                    args[0](*args[1:],**kwargs)
            elif callable(args[0]):
                for i in multi:
                    with self[i]:
                        args[0](i,*args[1:],**kwargs)
            elif len(args) > 1:
                env = self if args[0] is None else getattr(self,str(args[0]),None)
                if env is not None:
                    with env:
                        args[1](*args[2:],**kwargs)
        return self

def core_run(func):
    def wrap(*args, **kwargs):
        cfg = getattr(asm,'cfg',None)
        return func(*args, **kwargs) if cfg is None else cfg(func)(*args,**kwargs)
    return wrap

@core_run
def get_reg(rd,**kwargs):
    asm.dnld = kwargs.get('dnld',0)
    asm.rply = 1
    proc = kwargs.get('proc',None)
    if proc is not None:
        kwargs.pop('proc')
        asm.proc = lambda a, x: proc(x)
    rtlk_send(rd)

@core_run
def set_reg(rd,val):
    asm.dnld = 6
    mov(rd,val)

def get_err():
    err = get_reg('err',dnld=2)[0]
    print(f"ERR: 0x{err:X}")
    cfg = getattr(asm,'cfg',None)
    core = asm.core if cfg is None else cfg.core
    for i in range(len(core.T_ERR)):
        if err & (1<<i) != 0:
            print(f"{i:2}: {core.T_ERR[i]}")
    return err

def intf_run(func,sync=True):
    core = asm.core
    intf = getattr(asm, 'intf', None)
    if intf is None:
        cfg = getattr(asm, 'cfg', None)
        if cfg is None:
            return func
        intf = cfg.intf
        if cfg.core is not None:
            core = cfg.core
    oper = intf.oper.get((id(func)<<1)|sync,None)
    if oper is None:
        def cb(*args):
            if sync:
                with asm:
                    asm.core = core
                    adr = func(*args) or 0
                    intf.run(2,asm[:],adr)
                return True
            else:
                return func(*args)
        oper = len(intf.oper) + 1
        intf.oper[(id(func)<<1)|sync] = oper
        intf.oper[oper] = cb
    def wrap(*args,narg=None):
        if narg is None:
            narg = len(args)
        if hasattr(intf,'sn'):
            timer(300*1000)
            sleep()
        rtlk_send((narg<<20)|oper)
        if hasattr(intf,'sn'):
            timer(300*1000)
            sleep()
        for i in args:
            rtlk_send(i)
        if sync:
            smk('err','0x1.0','0x1.0')
    return wrap

intf_run_async = lambda func: intf_run(func,sync=False)

def segment(regs,vals,action=None):
    import base64
    tag = bytes([asm.core.regs[str(r)] for r in regs])
    if action is not None:
        tag += b'\x09' + id(action).to_bytes(8,'big')
    tag = base64.b64encode(tag).decode().rstrip('=')
    sub = getattr(asm,'sub',None)
    if sub is None:
        sub = {}
        asm.sub = sub
    n = len(regs)
    if sub.get(tag,None) is None:
        core = asm.core
        with asm:
            asm.core = core
            for i in range(n//7):
                for j in range(5):
                    add('dca','dca',j+1,B=0)
                add('dca','dca',5,B=0)
                add('dca','dca',5,B=0)
                for j in range(7):
                    mov(regs[7*i+j],'dcd',B=0)
            n %= 7
            if n == 0:
                if action is None:
                    mov('ptr','dcd',B=0)
                    add('dca','dca',1,B=0)
                    nop(7)
                elif callable(action):
                    action()
                else:
                    asm(*action)
            else:
                for j in range(n):
                    add('dca','dca',min(j+1,5),B=0)
                if action is None:
                    mov('ptr','dcd',B=0)
                    add('dca','dca',min(n+1,4),B=0)
                if n < 6:
                    nop((6 if action is None else 7)-n)
                for j in range(n):
                    mov(regs[-((n % 7)-j)],'dcd',B=0)
                if action is None:
                    nop()
                elif callable(action):
                    action()
                else:
                    asm(*action)
            sub[tag] = asm[:]
    dat = getattr(asm,'dat',None)
    if dat is None:
        dat = []
        asm.dat = dat
    if action is None and n > 0:
        dat += vals[:-n] + [None] + vals[-n:]
        return tag,len(dat)-1-n
    else:
        dat += vals + [None]
        return tag,len(dat)-1