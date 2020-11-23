from opentrons import protocol_api
from itertools import product

metadata = {'apiLevel': '2.7'}

wells = [i[0]+str(i[1]) for i in list(product(list('ABCDEFGH'), range(1,13)))]

def run(protocol: protocol_api.ProtocolContext):
    wellplate = protocol.load_labware('corning_96_wellplate_360ul_flat', 1)  #Polystyrene 96 well, flat bottom plate, max 323 ul?
    tiprack_1 = protocol.load_labware('opentrons_96_tiprack_300ul', 2) #small
    tiprack_2 = protocol.load_labware('opentrons_96_tiprack_300ul', 3) #big
    tuberack_s = protocol.load_labware('opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap', 4)
    tuberack_l = protocol.load_labware('opentrons_6_tuberack_falcon_50ml_conical', 5) # hebben we dat?
    resevoir = protocol.load_labware('axygen_1_reservoir_90ml', 6) #?
    p10 = protocol.load_instrument('p50_single', 'left', tip_racks=[tiprack_1]) #1-10
    p50 = protocol.load_instrument('p50_single', 'right', tip_racks=[tiprack_2]) #5-50
    #p300 = protocol.load_instrument('p300_single', 'left', tip_racks=[tiprack_2]) #30-300

    # CTAB
    #p50.pick_up_tip()
    #for _ in range(4):
    #    for w in wells:
    #        p50.aspirate(50, resevoir['A1'])
    #        p50.dispense(50, wellplate[w])
    #p50.return_tip()

    #HAuCl4
    #p10.pick_up_tip()
    #for w in wells:
    #    p10.aspirate(2, tuberack_s['A1'])
    #    p10.dispense(2, wellplate[w])
    #p10.return_tip()

    #AgNO3
    #p10.pick_up_tip()
    #volumes = [2,3,4,5]*8
    #for i, r in enumerate('ABCDEFGH'):
    #    volume_i = volumes[i]
    #    for c in range(1,13):
    #        w = r+str(c)
    #        v = volume_i
    #        while v>10: #if volume exceeds pipette volume
    #            p10.aspirate(10, tuberack_s['B1'])
    #            p10.dispense(10, wellplate[w])
    #            v -= 10
    #        p10.aspirate(v, tuberack_s['B1'])
    #        p10.dispense(v, wellplate[w])
    #p10.return_tip()    
    
    #Ascorbic Acid
    #p10.pick_up_tip()
    #for w in wells:
    #    p10.aspirate(1.6, tuberack_s['C1'])
    #    p10.dispense(1.6, wellplate[w])
    #p10.return_tip()

    #HCl
    p10.pick_up_tip()
    volumes = [1,3,5,10,15,20]*12
    for i, c in enumerate(range(1,13)):
        volume_i = volumes[i]
        for r in 'ABCDEFGH':
            w = r+str(c)
            v = volume_i
            while v>10: #if volume exceeds pipette volume
                p10.aspirate(10, tuberack_s['B1'])
                p10.dispense(10, wellplate[w])
                v -= 10
            p10.aspirate(v, tuberack_s['B1'])
            p10.dispense(v, wellplate[w])
    p10.return_tip()     

    #Seed
