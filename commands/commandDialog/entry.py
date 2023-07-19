import adsk.core
import os
import math
from ...lib import fusion360utils as futil
from ... import config
from .resources.ScrewSize import screewSize
app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'ScrewJoint'
CMD_Description = 'A Fusion 360 Add-in Command with a dialog'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.

    # Create a simple text box input.
    selectionInput = inputs.addSelectionInput('selection', 'Select', 'Basic select command input')
    selectionInput.setSelectionLimits(0)
    selectionInput.addSelectionFilter("CircularEdges")

    inputs.addTextBoxCommandInput('text_box', 'Some Text', 'Enter some text.', 1, False)
    dropdownInput = inputs.addDropDownCommandInput('head', 'Head type', adsk.core.DropDownStyles.TextListDropDownStyle)
    dropdownItems = dropdownInput.listItems
    dropdownItems.add('Socket', False, 'resources/Socket')
    dropdownItems.add('Rounded', False, 'resources/Rounded')
    dropdownItems.add('Hex', False, 'resources/Hex')
    dropdownItems.add('Flat', False, 'resources/Flat')


    dropdownInput2 = inputs.addDropDownCommandInput('thread', 'Thread', adsk.core.DropDownStyles.TextListDropDownStyle)
    dropdownItems2 = dropdownInput2.listItems

    for key,value in screewSize['hex'].items():
       dropdownItems2.add(key, False, 'resources/'+key)
    #    print(value)


    # for i in screewSize['hex'][1:]:
        
    




   
    # Create a value input field and set the default using 1 unit of the default length unit.
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    default_value = adsk.core.ValueInput.createByString('1')
    inputs.addValueInput('lenght', 'Lenght', defaultLengthUnits, default_value)

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.

    futil.log(f'{CMD_NAME} Command Execute Event')

    # TODO ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    selection : adsk.core.SelectionCommandInput = inputs.itemById('selection')
    text_box: adsk.core.TextBoxCommandInput = inputs.itemById('text_box')
    head: adsk.core.DropDownCommandInput = inputs.itemById('head')

    lenght: adsk.core.ValueCommandInput = inputs.itemById('lenght')
    thread: adsk.core.DropDownCommandInput = inputs.itemById('thread')

    circle=[]
    
    for i in range(selection.selectionCount):
        circle.append(selection.selection(i))
       
    headType = head.selectedItem.name


     
    # Do something interesting
    thread = thread.selectedItem.name

    text = text_box.text
    expression = lenght.expression
    des = adsk.fusion.Design.cast(app.activeProduct)
    for parent in circle:

        if headType == 'Hex':
            child = create_hex_screew(des, thread, expression)
        if headType == 'Rounded':
            create_rounded_screew(thread, expression)
        if headType == 'Flat':
            create_flat_screew(thread, expression)
        if headType == 'Socket':
            create_socket_screew(thread, expression)

        ui.messageBox(str(child.item(0)))

        # # Create the second joint geometry with the sketch line
        geo1 = adsk.fusion.JointGeometry.createByCurve(parent.entity, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        ui.messageBox('g1')

        geo0 = adsk.fusion.JointGeometry.createByCurve(child.item(0), adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
        
        ui.messageBox('g2')

        # Create joint input
        rootComp = des.rootComponent

        joints = rootComp.joints
        ui.messageBox('here')

        jointInput = joints.createInput(geo0, geo1)
        ui.messageBox('111')
        # Set the joint input
        angle = adsk.core.ValueInput.createByString('0 deg')
        jointInput.angle = angle
        jointInput.isFlipped = False
        jointInput.setAsRigidJointMotion()
        # Create the joint
        joint = joints.add(jointInput)

        # Lock the joint
        # joint.isLocked = True


    
    msg = f'Your text: {thread}{str(circle)}<br>Your value: {expression}'
    ui.messageBox(msg)


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    valueInput = inputs.itemById('value_input')
    if valueInput.value >= 0:
        args.areInputsValid = True
    else:
        args.areInputsValid = False
        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
def create_hex_screew(design, thread, lenght):
    ui.messageBox('1')
    bodyDiameter = screewSize['hex'][thread][0]/10
    headDiameter = screewSize['hex'][thread][1]/10
    headHeight = screewSize['hex'][thread][2]/10
    chamferDistance = screewSize['hex'][thread][3]/10
    cutAngle = screewSize['hex'][thread][4]/180*math.pi
    filletRadius = screewSize['hex'][thread][5]/10
    bodyLength = int(lenght.split(' ')[0])/10 + headHeight
    boltName = str(thread) + 'x' + str(int((bodyLength-headHeight)*10))

    try:
            occs = design.rootComponent.occurrences
            mat = adsk.core.Matrix3D.create()
            newOcc = occs.addNewComponent(mat)       
 
            newComp = adsk.fusion.Component.cast(newOcc.component)
            newComp.name = boltName

            if newComp is None:
                ui.messageBox('New component failed to create', 'New Component Failed')
                return

            # Create a new sketch.
            sketches = newComp.sketches
            xyPlane = newComp.xYConstructionPlane
            xzPlane = newComp.xZConstructionPlane
            sketch = sketches.add(xyPlane)
            center = adsk.core.Point3D.create(0, 0, 0)
            vertices = []
            for i in range(0, 6):
                vertex = adsk.core.Point3D.create(center.x + (headDiameter/2) * math.cos(math.pi * i / 3), center.y + (headDiameter/2) * math.sin(math.pi * i / 3),0)
                vertices.append(vertex)

            for i in range(0, 6):
                sketch.sketchCurves.sketchLines.addByTwoPoints(vertices[(i+1) %6], vertices[i])

            extrudes = newComp.features.extrudeFeatures
            prof = sketch.profiles[0]
            extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

            distance = adsk.core.ValueInput.createByReal(headHeight)
            extInput.setDistanceExtent(False, distance)
            headExt = extrudes.add(extInput)

            fc = headExt.faces[0]
            bd = fc.body
            bd.name = boltName

            #create the body


            bodySketch = sketches.add(xyPlane)
            bodySketch.sketchCurves.sketchCircles.addByCenterRadius(center, bodyDiameter/2)

            bodyProf = bodySketch.profiles[0]

            bodyExtInput = extrudes.createInput(bodyProf, adsk.fusion.FeatureOperations.JoinFeatureOperation)

            bodyExtInput.setAllExtent(adsk.fusion.ExtentDirections.NegativeExtentDirection)

            bodyExtInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(bodyLength))
            bodyExt = extrudes.add(bodyExtInput)

            # create chamfer

            edgeCol = adsk.core.ObjectCollection.create()
            edges = bodyExt.endFaces[0].edges
            for edgeI  in edges:
                edgeCol.add(edgeI)
            chamferFeats = newComp.features.chamferFeatures
            chamferInput = chamferFeats.createInput(edgeCol, True)
            chamferInput.setToEqualDistance(adsk.core.ValueInput.createByReal(chamferDistance))
            chamferFeats.add(chamferInput)

            # create fillet
            edgeCol.clear()
            loops = headExt.endFaces[0].loops
            edgeLoop = None
            for edgeLoop in loops:
                #since there two edgeloops in the start face of head, one consists of one circle edge while the other six edges
                if(len(edgeLoop.edges) == 1):
                    break

            edgeCol.add(edgeLoop.edges[0])  
            # filletFeats = newComp.features.filletFeatures
            # filletInput = filletFeats.createInput()
            # filletInput.addConstantRadiusEdgeSet(edgeCol, adsk.core.ValueInput.createByReal(filletRadius), True)
            # filletFeats.add(filletInput)

            #create revolve feature 1
            revolveSketchOne = sketches.add(xzPlane)
            radius = headDiameter/2
            point1 = revolveSketchOne.modelToSketchSpace(adsk.core.Point3D.create(center.x + radius*math.cos(math.pi/6), 0, center.y))
            ui.messageBox('stop')
            point2 = revolveSketchOne.modelToSketchSpace(adsk.core.Point3D.create(center.x + radius, 0, center.y))

            point3 = revolveSketchOne.modelToSketchSpace(adsk.core.Point3D.create(point2.x, 0, (point2.x - point1.x) * math.tan(cutAngle)))
            revolveSketchOne.sketchCurves.sketchLines.addByTwoPoints(point1, point2)
            revolveSketchOne.sketchCurves.sketchLines.addByTwoPoints(point2, point3)
            revolveSketchOne.sketchCurves.sketchLines.addByTwoPoints(point3, point1)

            #revolve feature 2
            revolveSketchTwo = sketches.add(xzPlane)
            point4 = revolveSketchTwo.modelToSketchSpace(adsk.core.Point3D.create(center.x + radius*math.cos(math.pi/6), 0, headHeight - center.y))
            point5 = revolveSketchTwo.modelToSketchSpace(adsk.core.Point3D.create(center.x + radius, 0, headHeight - center.y))
            point6 = revolveSketchTwo.modelToSketchSpace(adsk.core.Point3D.create(center.x + point2.x, 0, headHeight - center.y - (point5.x - point4.x) * math.tan(cutAngle)))
            revolveSketchTwo.sketchCurves.sketchLines.addByTwoPoints(point4, point5)
            revolveSketchTwo.sketchCurves.sketchLines.addByTwoPoints(point5, point6)
            revolveSketchTwo.sketchCurves.sketchLines.addByTwoPoints(point6, point4)

            zaxis = newComp.zConstructionAxis
            revolves = newComp.features.revolveFeatures
            revProf1 = revolveSketchTwo.profiles[0]
            revInput1 = revolves.createInput(revProf1, zaxis, adsk.fusion.FeatureOperations.CutFeatureOperation)

            revAngle = adsk.core.ValueInput.createByReal(math.pi*2)
            revInput1.setAngleExtent(False,revAngle)
            revolves.add(revInput1)

            revProf2 = revolveSketchOne.profiles[0]
            revInput2 = revolves.createInput(revProf2, zaxis, adsk.fusion.FeatureOperations.CutFeatureOperation)

            revInput2.setAngleExtent(False,revAngle)
            revolves.add(revInput2)
            
            sideFace = bodyExt.sideFaces[0]
            threads = newComp.features.threadFeatures
            threadDataQuery = threads.threadDataQuery
            defaultThreadType = threadDataQuery.defaultMetricThreadType
            recommendData = threadDataQuery.recommendThreadData(bodyDiameter, False, defaultThreadType)
            if recommendData[0] :
                threadInfo = threads.createThreadInfo(False, defaultThreadType, recommendData[1], recommendData[2])
                faces = adsk.core.ObjectCollection.create()
                faces.add(sideFace)
                threadInput = threads.createInput(faces, threadInfo)
                threads.add(threadInput)
            
            # edgeCol.clear()
            # loops = headExt.endFaces[0].loops
            # edgeLoop = None
            # for edgeLoop in loops:
            #     #since there two edgeloops in the start face of head, one consists of one circle edge while the other six edges
            #     if(len(edgeLoop.edges) == 1):
            #         break
            # edgeCol.add(edgeLoop.edges[0])  

            return (edgeCol)
            

    except:
            if ui:
                ui.messageBox('Failed to compute the bolt. This is most likely because the input values define an invalid bolt.')


    return
def create_rounded_screew(diam, lenght):
    ui.messageBox(str(diam)+' '+str(lenght)+' rounded')
    return
def create_flat_screew(diam, lenght):
    ui.messageBox(str(diam)+' '+str(lenght)+' flat')
    return
def create_socket_screew(diam, lenght):
    ui.messageBox(str(diam)+' '+str(lenght)+' socket')
    return