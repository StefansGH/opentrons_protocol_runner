import json
import opentrons.simulate
import opentrons.execute
import socket
import sys
import random
import math

host = str(sys.argv[1]) #ip
port = 65432

opentrons_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
opentrons_socket.bind((host, port))

data, _ = opentrons_socket.recvfrom(1024)
data = data.decode('utf-8').split(',') #data is a string "material,units,simulate,well,close,return_tips,starting_tip_10,starting_tip_50,mix
simulate = data[3]=="True"

if not simulate:
    protocol = opentrons.execute.get_protocol_api('2.8')
else:
    protocol = opentrons.simulate.get_protocol_api('2.8')

return_tips = data[6]=="True"

### tuberack ###
with open('src/hardware/smartprobes_24_tuberack_eppendorf_2ml_safelock_snapcap.json') as labware_file:
    smartprobes_tuberack = json.load(labware_file)
tuberack = protocol.load_labware_from_definition(smartprobes_tuberack, 1)

with open('src/materials/tuberack.json') as materials_file:
    tuberack_materials = json.load(materials_file)

def find_tube_with_enough_volume(material, concentration, volume):
    tube_idx = 0
    tube_label = list(tuberack_materials)[tube_idx] #eg 'B3'
    while (tuberack_materials[tube_label]['material']!=material) | (tuberack_materials[tube_label]['concentration']!=concentration) | (volume>tuberack_materials[tube_label]['volume']):
        tube_idx += 1
        tube_label = list(tuberack_materials)[tube_idx]
    return tube_label

def update_tuberack_volumes(tuberack_materials, tube_label, volume):
    tuberack_materials[tube_label]['volume'] = tuberack_materials[tube_label]['volume'] - volume
    return tuberack_materials

### pipette/tips ###
with open('src/hardware/smartprobes_96_tiprack_10ul.json') as labware_file:
    smartprobes_tiprack_10 = json.load(labware_file)
tiprack_10 = protocol.load_labware_from_definition(smartprobes_tiprack_10, 2)

with open('src/hardware/smartprobes_96_tiprack_200ul.json') as labware_file:
    smartprobes_tiprack_200 = json.load(labware_file)
tiprack_200 = protocol.load_labware_from_definition(smartprobes_tiprack_200, 5)

p10 = protocol.load_instrument('p10_single', 'left', tip_racks=[tiprack_10]) #1-10
p10.well_bottom_clearance.aspirate = -1
p10.well_bottom_clearance.dispense = -1
p10.starting_tip = tiprack_10.well(data[7])

p50 = protocol.load_instrument('p50_single', 'right', tip_racks=[tiprack_200]) #5-50
p50.well_bottom_clearance.aspirate = 5
p50.well_bottom_clearance.dispense = 5
p50.starting_tip = tiprack_200.well(data[8])

### wellplate ###
with open('src/hardware/smartprobes_96_wellplate_200ul_flat.json') as labware_file:
    smartprobes_wellplate = json.load(labware_file)
wellplate = protocol.load_labware_from_definition(smartprobes_wellplate, 3)

protocol_lentgh = 0
volume_in_well = {}

### protocol ###
protocol.home()
while data[5]=='False': #intil close==True
    material = data[0]
    concentration = float(data[1])
    volume = float(data[2])
    well_label = int(data[4])
    well = wellplate.wells()[well_label]
    
    if data[9]=='True': #mix
        pipette = p50
        pipette.flow_rate.dispense = 500
        pipette.pick_up_tip()
        volume_hight = (volume_in_well[well_label]-50) / (math.pi*((well.diameter/2)**2))
        for _ in range(10):
            pipette.aspirate(volume=50, location=well.bottom(z=volume_hight*random.random()))
            pipette.dispense(volume=50, location=well.bottom(z=volume_hight*random.random()))
        if return_tips:
            pipette.return_tip()
        else:
            pipette.drop_tip() #thrash

    else: #pipette

        if volume <= 10: 
            pipette, pipette_max_volume = p10, 10
            pipette.flow_rate.dispense = 20
            
        else:
            pipette, pipette_max_volume = p50, 50
            pipette.flow_rate.dispense = 100

        if (material, concentration) not in [(tuberack_materials[w]['material'], tuberack_materials[w]['concentration']) for w in list(tuberack_materials)]: #check for wrongwriting in materials
            print(str(material) + ' ' + str(concentration) + ' not in tuberack!')
        tube_label = find_tube_with_enough_volume(material, concentration, volume)
        tube, tube_volume = tube_label, tuberack_materials[tube_label]['volume']

        remaining_volume_to_pipette = volume
        while remaining_volume_to_pipette>0:
            pipette.pick_up_tip()
            v = min(pipette_max_volume, remaining_volume_to_pipette)
            tuberack_materials = update_tuberack_volumes(tuberack_materials, tube_label, v)
            remaining_volume_to_pipette -= v
            pipette.aspirate(v, tuberack[tube].bottom())
            pipette.dispense(v, well)
            pipette.blow_out(well)
            pipette.touch_tip(well, v_offset=-5, radius=1.3)
            pipette.blow_out(well)
            volume -= pipette_max_volume

            if well_label not in volume_in_well:
                volume_in_well[well_label] = v
            else:
                volume_in_well[well_label] = volume_in_well[well_label] + v

            if return_tips:
                pipette.return_tip()
            else:
                pipette.drop_tip() #thrash

    data, _ = opentrons_socket.recvfrom(1024) #get next action from server
    data = data.decode('utf-8').split(',')

    print("\n".join(protocol._commands[protocol_lentgh:]))
    protocol_lentgh = len(protocol._commands)

protocol.home()
opentrons_socket.close()
