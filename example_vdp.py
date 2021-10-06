import instruments
import time

sb = instruments.SwitchBox()
pg = instruments.K2461()
bb = instruments.BalanceBox()
sb.connect(4)
pg.connect()
bb.connect(5)
bb.enable_all()
bb.reset_resistances()

vert1_ass = {"I+": "B", "I-": "D", "V2+": "F", "V2-": "H"}
vert2_ass = {"I+": "F", "I-": "H", "V2+": "B", "V2-": "D"}
vert3_ass = {"I+": "D", "I-": "B", "V2+": "H", "V2-": "F"}
vert4_ass = {"I+": "H", "I-": "F", "V2+": "D", "V2-": "B"}
hor1_ass = {"I+": "B", "I-": "H", "V2+": "F", "V2-": "D"}
hor2_ass = {"I+": "F", "I-": "D", "V2+": "B", "V2-": "H"}
hor3_ass = {"I+": "H", "I-": "B", "V2+": "D", "V2-": "F"}
hor4_ass = {"I+": "D", "I-": "F", "V2+": "H", "V2-": "B"}

sb.switch(vert1_ass)
time.sleep(1)
pg.enable_4_wire_probe(1e-3)
time.sleep(1)
c, v = pg.read_one()
Rver1 = v / c
pg.disable_probe_current()
print(f'Vert1: {Rver1}')

sb.switch(vert2_ass)
time.sleep(1)
pg.enable_4_wire_probe(1e-3)
time.sleep(1)
c, v = pg.read_one()
Rver2 = v / c
pg.disable_probe_current()
print(f'Vert2: {Rver2}')

sb.switch(vert3_ass)
time.sleep(1)
pg.enable_4_wire_probe(1e-3)
time.sleep(1)
c, v = pg.read_one()
Rver3 = v / c
pg.disable_probe_current()
print(f'Vert3: {Rver3}')

sb.switch(vert4_ass)
time.sleep(1)
pg.enable_4_wire_probe(1e-3)
time.sleep(1)
c, v = pg.read_one()
Rver4 = v / c
pg.disable_probe_current()
print(f'Vert4: {Rver4}')

sb.switch(hor1_ass)
time.sleep(1)
pg.enable_4_wire_probe(1e-3)
time.sleep(1)
c, v = pg.read_one()
Rhor1 = v / c
print(f'Vhor1: {Rhor1}')
pg.disable_probe_current()

sb.switch(hor2_ass)
time.sleep(1)
pg.enable_4_wire_probe(1e-3)
time.sleep(1)
c, v = pg.read_one()
Rhor2 = v / c
print(f'Vhor2: {Rhor2}')
pg.disable_probe_current()

sb.switch(hor3_ass)
time.sleep(1)
pg.enable_4_wire_probe(1e-3)
time.sleep(1)
c, v = pg.read_one()
Rhor3 = v / c
print(f'Vhor3: {Rhor3}')
pg.disable_probe_current()

sb.switch(hor4_ass)
time.sleep(1)
pg.enable_4_wire_probe(1e-3)
time.sleep(1)
c, v = pg.read_one()
Rhor4 = v / c
print(f'Vhor4: {Rhor4}')
pg.disable_probe_current()

Rvertical = (Rver1 + Rver2 + Rver3 + Rver4) / 4
Rhorizontal = (Rhor1 + Rhor2 + Rhor3 + Rhor4) / 4
print(f'Rvert: {Rvertical}, Rhor: {Rhorizontal}')
