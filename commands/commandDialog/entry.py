import adsk.core
import os
import math
import traceback
from ...lib import fusion360utils as futil
from ... import config
from .resources.ScrewSize import screewSize
app = adsk.core.Application.get()
ui = app.userInterface
des = adsk.fusion.Design.cast(app.activeProduct)
   
importManager = app.importManager 
            # Get active design
   
            
            # Get root component
rootComp = des.rootComponent


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'ScrewAssembler'
CMD_Description = 'Add multiply screw joints'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'AssemblePanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

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
    selectionInput = inputs.addSelectionInput(
        'selection', 'Select', 'Basic select command input')
    selectionInput.setSelectionLimits(0)
    selectionInput.addSelectionFilter("CircularEdges")

    # inputs.addTextBoxCommandInput(
    #     'text_box', 'Some Text', 'Enter some text.', 1, False)
    dropdownInput = inputs.addDropDownCommandInput(
        'head', 'Head type', adsk.core.DropDownStyles.TextListDropDownStyle)
    dropdownItems = dropdownInput.listItems
    
    dropdownItems.add('Socket', False, 'resources/Socket')
    dropdownItems.add('Rounded', False, 'resources/Rounded')
    dropdownItems.add('Hex', False, 'resources/Hex')
    dropdownItems.add('Flat', False, 'resources/Flat')

    slot = inputs.addDropDownCommandInput(
        'head_slot', 'Head slot', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
    slot.isVisible = False
    

    
    thread = inputs.addDropDownCommandInput(
        'thread', 'Thread', adsk.core.DropDownStyles.TextListDropDownStyle)
    thread.isVisible = False

    # dropdownItems2 = dropdownInput2.listItems

    # for key, value in screewSize['hex'].items():
    #     dropdownItems2.add(key, False, 'resources/'+key)
    
    # Create a value input field and set the default using 1 unit of the default length unit.
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    default_value = adsk.core.ValueInput.createByString('1')
    lenght = inputs.addValueInput('lenght', 'Lenght', defaultLengthUnits, default_value)
    lenght.isVisible = False
    flip = inputs.addBoolValueInput("flip", "Flip", True)
    flip.isVisible = False

    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute,
                      local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged,
                      command_input_changed, local_handlers=local_handlers)
    # futil.add_handler(args.command.executePreview,
    #                   command_preview, local_handlers=local_handlers)
    # futil.add_handler(args.command.validateInputs,
    #                   command_validate_input, local_handlers=local_handlers)
    # futil.add_handler(args.command.destroy, command_destroy,
    #                   local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')
    # TODO ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    selection: adsk.core.SelectionCommandInput = inputs.itemById('selection')
    # text_box: adsk.core.TextBoxCommandInput = inputs.itemById('text_box')
    head: adsk.core.DropDownCommandInput = inputs.itemById('head')
    headslot: adsk.core.DropDownCommandInput = inputs.itemById('head_slot')
    lenght: adsk.core.ValueCommandInput = inputs.itemById('lenght')
    thread: adsk.core.DropDownCommandInput = inputs.itemById('thread')
    flip: adsk.core.BoolValueCommandInput = inputs.itemById('flip')

    circle = []

    for i in range(selection.selectionCount):
        circle.append(selection.selection(i))

    headType = head.selectedItem.name
    headSlot = headslot.selectedItem.name
    # Do something interesting
    thread = thread.selectedItem.name

    expression = lenght.expression
    screw, leng = createScrew(headType, thread, expression, headSlot)
    bodyInSubComp1 = screw.bRepBodies.item(0)

    # ui.messageBox(str(screw))
    for parent in circle:
        newScrewComp = rootComp.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        newScrewComp.component.name = f'Screw {thread}x{expression}'
        newScrew = newScrewComp.component.features.copyPasteBodies.add(bodyInSubComp1)
        for i in range(newScrew.bodies.item(0).faces.count):
            face = newScrew.bodies.item(0).faces.item(i)
            if abs(face.centroid.z)<0.001 :
            # if face.centroid.asArray() == [0,0,0] :
               
                child = face.edges.item(0)
           

        # # Create the second joint geometry with the sketch line
        geo1 = adsk.fusion.JointGeometry.createByCurve(
            parent.entity, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)

        geo0 = adsk.fusion.JointGeometry.createByCurve(
            child, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)


        joints = rootComp.joints
        # ui.messageBox('here')

        jointInput = joints.createInput(geo0, geo1)
        # Set the joint input
        angle = adsk.core.ValueInput.createByString('0 deg')
        jointInput.angle = angle
        jointInput.isFlipped = not flip.value
        jointInput.setAsRigidJointMotion()
        # Create the joint
        joint = joints.add(jointInput)
    occurrences = rootComp.allOccurrencesByComponent(screw)
    features = rootComp.features
    removeFeatures = features.removeFeatures
    
    for occurrence in occurrences:
        removeFeatures.add(occurrence)


            # Delete them.
    # for uniqueOccurrencesI in uniqueOccurrences:
    #             uniqueOccurrencesI.deleteMe()
    # screw.deleteMe()

        # Lock the joint
        # joint.isLocked = True


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

    if changed_input.id == "head":
        
        slot = inputs.itemById('head_slot')
        thread = inputs.itemById('thread')

        slotItems = slot.listItems
        slotItems.clear()
        
        threadItems = thread.listItems
        threadItems.clear()

        lenght = inputs.itemById('lenght')
        flip = inputs.itemById('flip')

        if changed_input.selectedItem.name == "Rounded":
            slotItems.add('Torx', False, os.path.join(ICON_FOLDER,'Slot','Torx'))
            slotItems.add('Hex', False, os.path.join(ICON_FOLDER,'Slot','Hex'))
            slotItems.add('Philips', False, os.path.join(ICON_FOLDER,'Slot','Philips'))

            for i in ['M2','M2.5','M3','M4','M5', 'M6', 'M8', 'M10']:
                threadItems.add(i, False, 'resourse/')


            
        if changed_input.selectedItem.name == "Socket":
            slotItems.add('Torx', False, os.path.join(ICON_FOLDER,'Slot','Torx'))
            slotItems.add('Hex', False, os.path.join(ICON_FOLDER,'Slot','Hex'))

            for i in ['M2','M2.5','M3','M4','M5', 'M6', 'M8', 'M10', 'M12', 'M14', 'M16','M18', 'M20', 'M22', 'M24']:
                threadItems.add(i, False, 'resourse/')

        if changed_input.selectedItem.name == "Flat":
            slotItems.add('Torx', False, os.path.join(ICON_FOLDER,'Slot','Torx'))
            slotItems.add('Hex', False, os.path.join(ICON_FOLDER,'Slot','Hex'))
            slotItems.add('Philips', False, os.path.join(ICON_FOLDER,'Slot','Philips'))
        
        if changed_input.selectedItem.name == "Hex": 
            slotItems.add('Hex', False, os.path.join(ICON_FOLDER,'Slot','Hex'))
            slotItems.add('Philips', False, os.path.join(ICON_FOLDER,'Slot','Philips'))
        slot.isVisible = True
        thread.isVisible = True
        lenght.isVisible = True
        flip.isVisible = True


    # General logging for debug.
    futil.log(
        f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


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
            ui.messageBox('New component failed to create',
                          'New Component Failed')
            return

        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        xzPlane = newComp.xZConstructionPlane
        sketch = sketches.add(xyPlane)
        center = adsk.core.Point3D.create(0, 0, 0)
        vertices = []
        for i in range(0, 6):
            vertex = adsk.core.Point3D.create(center.x + (headDiameter/2) * math.cos(
                math.pi * i / 3), center.y + (headDiameter/2) * math.sin(math.pi * i / 3), 0)
            vertices.append(vertex)

        for i in range(0, 6):
            sketch.sketchCurves.sketchLines.addByTwoPoints(
                vertices[(i+1) % 6], vertices[i])

        extrudes = newComp.features.extrudeFeatures
        prof = sketch.profiles[0]
        extInput = extrudes.createInput(
            prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        distance = adsk.core.ValueInput.createByReal(headHeight)
        extInput.setDistanceExtent(False, distance)
        headExt = extrudes.add(extInput)

        fc = headExt.faces[0]
        bd = fc.body
        bd.name = boltName

        # create the body

        bodySketch = sketches.add(xyPlane)
        bodySketch.sketchCurves.sketchCircles.addByCenterRadius(
            center, bodyDiameter/2)

        bodyProf = bodySketch.profiles[0]

        bodyExtInput = extrudes.createInput(
            bodyProf, adsk.fusion.FeatureOperations.JoinFeatureOperation)

        bodyExtInput.setAllExtent(
            adsk.fusion.ExtentDirections.NegativeExtentDirection)

        bodyExtInput.setDistanceExtent(
            False, adsk.core.ValueInput.createByReal(bodyLength))
        bodyExt = extrudes.add(bodyExtInput)

        # create chamfer

        edgeCol = adsk.core.ObjectCollection.create()
        edges = bodyExt.endFaces[0].edges
        for edgeI in edges:
            edgeCol.add(edgeI)
        chamferFeats = newComp.features.chamferFeatures
        chamferInput = chamferFeats.createInput(edgeCol, True)
        chamferInput.setToEqualDistance(
            adsk.core.ValueInput.createByReal(chamferDistance))
        chamferFeats.add(chamferInput)

        # create fillet
        edgeCol.clear()
        loops = headExt.endFaces[0].loops
        edgeLoop = None
        for edgeLoop in loops:
            # since there two edgeloops in the start face of head, one consists of one circle edge while the other six edges
            if (len(edgeLoop.edges) == 1):
                break

        edgeCol.add(edgeLoop.edges[0])
        # filletFeats = newComp.features.filletFeatures
        # filletInput = filletFeats.createInput()
        # filletInput.addConstantRadiusEdgeSet(edgeCol, adsk.core.ValueInput.createByReal(filletRadius), True)
        # filletFeats.add(filletInput)

        # create revolve feature 1
        revolveSketchOne = sketches.add(xzPlane)
        radius = headDiameter/2
        point1 = revolveSketchOne.modelToSketchSpace(adsk.core.Point3D.create(
            center.x + radius*math.cos(math.pi/6), 0, center.y))
        point2 = revolveSketchOne.modelToSketchSpace(
            adsk.core.Point3D.create(center.x + radius, 0, center.y))

        point3 = revolveSketchOne.modelToSketchSpace(adsk.core.Point3D.create(
            point2.x, 0, (point2.x - point1.x) * math.tan(cutAngle)))
        revolveSketchOne.sketchCurves.sketchLines.addByTwoPoints(
            point1, point2)
        revolveSketchOne.sketchCurves.sketchLines.addByTwoPoints(
            point2, point3)
        revolveSketchOne.sketchCurves.sketchLines.addByTwoPoints(
            point3, point1)

        # revolve feature 2
        revolveSketchTwo = sketches.add(xzPlane)
        point4 = revolveSketchTwo.modelToSketchSpace(adsk.core.Point3D.create(
            center.x + radius*math.cos(math.pi/6), 0, headHeight - center.y))
        point5 = revolveSketchTwo.modelToSketchSpace(
            adsk.core.Point3D.create(center.x + radius, 0, headHeight - center.y))
        point6 = revolveSketchTwo.modelToSketchSpace(adsk.core.Point3D.create(
            center.x + point2.x, 0, headHeight - center.y - (point5.x - point4.x) * math.tan(cutAngle)))
        revolveSketchTwo.sketchCurves.sketchLines.addByTwoPoints(
            point4, point5)
        revolveSketchTwo.sketchCurves.sketchLines.addByTwoPoints(
            point5, point6)
        revolveSketchTwo.sketchCurves.sketchLines.addByTwoPoints(
            point6, point4)

        zaxis = newComp.zConstructionAxis
        revolves = newComp.features.revolveFeatures
        ui.messageBox(str(bd))

        revProf1 = revolveSketchTwo.profiles[0]
        revInput1 = revolves.createInput(
            revProf1, zaxis, adsk.fusion.FeatureOperations.CutFeatureOperation)

        bodys = []
        bodys.append(headExt)

        revAngle = adsk.core.ValueInput.createByReal(math.pi*2)
        revInput1.setAngleExtent(False, revAngle)
        ui.messageBox(str(revInput1.participantBodies))

        revInput1.participantBodies = bodys
        revolves.add(revInput1)

        revProf2 = revolveSketchOne.profiles[0]
        revInput2 = revolves.createInput(
            revProf2, zaxis, adsk.fusion.FeatureOperations.CutFeatureOperation)

        revInput2.setAngleExtent(False, revAngle)
        revInput2.participantBodies = bodys

        revolves.add(revInput2)

        sideFace = bodyExt.sideFaces[0]
        threads = newComp.features.threadFeatures
        threadDataQuery = threads.threadDataQuery
        defaultThreadType = threadDataQuery.defaultMetricThreadType
        recommendData = threadDataQuery.recommendThreadData(
            bodyDiameter, False, defaultThreadType)
        if recommendData[0]:
            threadInfo = threads.createThreadInfo(
                False, defaultThreadType, recommendData[1], recommendData[2])
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
            ui.messageBox(
                'Failed to compute the bolt. This is most likely because the input values define an invalid bolt.')
    return


def create_rounded_screew(design, thread, lenght):

    bodyDiameter = screewSize['rounded'][thread][0]/10
    headDiameter = screewSize['rounded'][thread][1]/10
    headHeight = screewSize['rounded'][thread][2]/10
    headRound = screewSize['rounded'][thread][3]/10
    chamferDistance = screewSize['rounded'][thread][4]/10
    cutAngle = screewSize['rounded'][thread][5]/180*math.pi

    bodyLength = int(lenght.split(' ')[0])/10 + headHeight
    boltName = str(thread) + 'x' + str(int((bodyLength-headHeight)*10))

    try:
        occs = design.rootComponent.occurrences
        mat = adsk.core.Matrix3D.create()
        newOcc = occs.addNewComponent(mat)

        newComp = adsk.fusion.Component.cast(newOcc.component)
        newComp.name = boltName

        if newComp is None:
            ui.messageBox('New component failed to create',
                          'New Component Failed')
            return

        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        xzPlane = newComp.xZConstructionPlane
        sketch = sketches.add(xyPlane)
        center = adsk.core.Point3D.create(0, 0, 0)

        # sketch.sketchCircles.addByCenterRadius(center, headRound)

        vertices = []
        vertex = adsk.core.Point3D.create(
            center.x + headDiameter/2, center.y + headRound, 0)
        vertices.append(vertex)
        vertex = adsk.core.Point3D.create(
            center.x + headDiameter/2, center.y - headRound, 0)
        vertices.append(vertex)

        for i in range(0, 2):
            sketch.sketchCurves.sketchLines.addByTwoPoints(
                vertices[(i+1) % 2], vertices[i])

        vertices = []
        vertex = adsk.core.Point3D.create(
            center.x - headDiameter/2, center.y + headRound, 0)
        vertices.append(vertex)
        vertex = adsk.core.Point3D.create(
            center.x - headDiameter/2, center.y - headRound, 0)
        vertices.append(vertex)

        for i in range(0, 2):
            sketch.sketchCurves.sketchLines.addByTwoPoints(
                vertices[(i+1) % 2], vertices[i])

        sketch.sketchCurves.sketchCircles.addByCenterRadius(
            center, headRound)

        # extrudes = newComp.features.extrudeFeatures
        # prof = sketch.profiles[0]
        # extInput = extrudes.createInput(
        #     prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

        # distance = adsk.core.ValueInput.createByReal(headHeight)
        # extInput.setDistanceExtent(False, distance)
        # headExt = extrudes.add(extInput)

        # fc = headExt.faces[0]
        # bd = fc.body
        # bd.name = boltName

        # # create the body

        # bodySketch = sketches.add(xyPlane)
        # bodySketch.sketchCurves.sketchCircles.addByCenterRadius(
        #     center, bodyDiameter/2)

        # bodyProf = bodySketch.profiles[0]

        # bodyExtInput = extrudes.createInput(
        #     bodyProf, adsk.fusion.FeatureOperations.JoinFeatureOperation)

        # bodyExtInput.setAllExtent(
        #     adsk.fusion.ExtentDirections.NegativeExtentDirection)

        # bodyExtInput.setDistanceExtent(
        #     False, adsk.core.ValueInput.createByReal(bodyLength))
        # bodyExt = extrudes.add(bodyExtInput)

        # # create chamfer

        # edgeCol = adsk.core.ObjectCollection.create()
        # edges = bodyExt.endFaces[0].edges
        # for edgeI in edges:
        #     edgeCol.add(edgeI)
        # chamferFeats = newComp.features.chamferFeatures
        # chamferInput = chamferFeats.createInput(edgeCol, True)
        # chamferInput.setToEqualDistance(
        #     adsk.core.ValueInput.createByReal(chamferDistance))
        # chamferFeats.add(chamferInput)

        # # create fillet
        # edgeCol.clear()
        # loops = headExt.endFaces[0].loops
        # edgeLoop = None
        # for edgeLoop in loops:
        # since there two edgeloops in the start face of head, one consists of one circle edge while the other six edges
        #     if (len(edgeLoop.edges) == 1):
        #         break

        # edgeCol.add(edgeLoop.edges[0])
        # filletFeats = newComp.features.filletFeatures
        # filletInput = filletFeats.createInput()
        # filletInput.addConstantRadiusEdgeSet(edgeCol, adsk.core.ValueInput.createByReal(filletRadius), True)
        # filletFeats.add(filletInput)

        # create revolve feature 1
        # revolveSketchOne = sketches.add(xzPlane)
        # radius = headDiameter/2
        # point1 = revolveSketchOne.modelToSketchSpace(adsk.core.Point3D.create(
        #     center.x + radius*math.cos(math.pi/6), 0, center.y))
        # point2 = revolveSketchOne.modelToSketchSpace(
        #     adsk.core.Point3D.create(center.x + radius, 0, center.y))

        # point3 = revolveSketchOne.modelToSketchSpace(adsk.core.Point3D.create(
        #     point2.x, 0, (point2.x - point1.x) * math.tan(cutAngle)))
        # revolveSketchOne.sketchCurves.sketchLines.addByTwoPoints(
        #     point1, point2)
        # revolveSketchOne.sketchCurves.sketchLines.addByTwoPoints(
        #     point2, point3)
        # revolveSketchOne.sketchCurves.sketchLines.addByTwoPoints(
        #     point3, point1)

        # # revolve feature 2
        # revolveSketchTwo = sketches.add(xzPlane)
        # point4 = revolveSketchTwo.modelToSketchSpace(adsk.core.Point3D.create(
        #     center.x + radius*math.cos(math.pi/6), 0, headHeight - center.y))
        # point5 = revolveSketchTwo.modelToSketchSpace(
        #     adsk.core.Point3D.create(center.x + radius, 0, headHeight - center.y))
        # point6 = revolveSketchTwo.modelToSketchSpace(adsk.core.Point3D.create(
        #     center.x + point2.x, 0, headHeight - center.y - (point5.x - point4.x) * math.tan(cutAngle)))
        # revolveSketchTwo.sketchCurves.sketchLines.addByTwoPoints(
        #     point4, point5)
        # revolveSketchTwo.sketchCurves.sketchLines.addByTwoPoints(
        #     point5, point6)
        # revolveSketchTwo.sketchCurves.sketchLines.addByTwoPoints(
        #     point6, point4)

        # zaxis = newComp.zConstructionAxis
        # revolves = newComp.features.revolveFeatures
        # revProf1 = revolveSketchTwo.profiles[0]
        # revInput1 = revolves.createInput(
        #     revProf1, zaxis, adsk.fusion.FeatureOperations.CutFeatureOperation)

        # revAngle = adsk.core.ValueInput.createByReal(math.pi*2)
        # revInput1.setAngleExtent(False, revAngle)
        # revolves.add(revInput1)

        # revProf2 = revolveSketchOne.profiles[0]
        # revInput2 = revolves.createInput(
        #     revProf2, zaxis, adsk.fusion.FeatureOperations.CutFeatureOperation)

        # revInput2.setAngleExtent(False, revAngle)
        # revolves.add(revInput2)

        # sideFace = bodyExt.sideFaces[0]
        # threads = newComp.features.threadFeatures
        # threadDataQuery = threads.threadDataQuery
        # defaultThreadType = threadDataQuery.defaultMetricThreadType
        # recommendData = threadDataQuery.recommendThreadData(
        #     bodyDiameter, False, defaultThreadType)
        # if recommendData[0]:
        #     threadInfo = threads.createThreadInfo(
        #         False, defaultThreadType, recommendData[1], recommendData[2])
        #     faces = adsk.core.ObjectCollection.create()
        #     faces.add(sideFace)
        #     threadInput = threads.createInput(faces, threadInfo)
        #     threads.add(threadInput)

        # edgeCol.clear()
        # loops = headExt.endFaces[0].loops
        # edgeLoop = None
        # for edgeLoop in loops:
        #     #since there two edgeloops in the start face of head, one consists of one circle edge while the other six edges
        #     if(len(edgeLoop.edges) == 1):
        #         break
        # edgeCol.add(edgeLoop.edges[0])

        # return (edgeCol)

    except:
        if ui:
            ui.messageBox(
                'Failed to compute the bolt. This is most likely because the input values define an invalid bolt.')

    return


def create_flat_screew(diam, lenght):
    ui.messageBox(str(diam)+' '+str(lenght)+' flat')
    return


def create_socket_screew(diam, lenght):
    ui.messageBox(str(diam)+' '+str(lenght)+' socket')
    return


def normalVector(edge):

    face = edge.faces.item(1)

    if face.geometry.surfaceType != 0:
        face = edge.faces.item(0)

    point = face.centroid

    des = adsk.fusion.Design.cast(app.activeProduct)
    rootComp = des.rootComponent

    planes = rootComp.constructionPlanes
    planeInput = planes.createInput()

    offsetValue = adsk.core.ValueInput.createByReal(3.0)
    planeInput.setByOffset(face, offsetValue)
    planeOne = planes.add(planeInput)

    measureManager = app.measureManager
    measureResult = measureManager.measureMinimumDistance(point, planeOne)
    point1 = measureResult.positionOne
    point2 = measureResult.positionTwo

    vectorToFace = point2.vectorTo(point1)
    # ui.messageBox('1')
    planeOne.deleteMe()

    _, normVector = face.evaluator.getNormalAtPoint(point)
    return vectorToFace, normVector

    # crossProduct = normalAtFace.crossProduct(vectorToFace)


def createScrew(headType, thread, lenght, headSlot):
    bodyDiameter = screewSize['hex'][thread][0]/10
    # headDiameter = screewSize['hex'][thread][1]/10
    # headHeight = screewSize['hex'][thread][2]/10
    chamferDistance = bodyDiameter/10
    # cutAngle = screewSize['hex'][thread][4]/180*math.pi
    # filletRadius = screewSize['hex'][thread][5]/10
    bodyLength = int(lenght.split(' ')[0])/10
    boltName = str(thread) + 'x' + str(int((bodyLength)*10))
  
    # ui.messageBox('1')
    # app = adsk.core.Application.get()
    # importManager = app.importManager 
    #         # Get active design
    # product = app.activeProduct
    # design = adsk.fusion.Design.cast(product)
            
    #         # Get root component


  

    archiveFileName = os.path.join(ICON_FOLDER,'Screw',headType,headSlot,thread+".f3d")

    # archiveFileName = './Screew/Rounded/Torx/M2.f3d'
    archiveOptions = importManager.createFusionArchiveImportOptions(
        archiveFileName)
    
    # Import archive file to root component
    try:
        head = importManager.importToTarget2(archiveOptions, rootComp)
    except: 
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    headComp = head.item(0).component
    headComp.name = boltName


    sketches = headComp.sketches
    xyPlane = headComp.xYConstructionPlane
    xzPlane = headComp.xZConstructionPlane
    sketch = sketches.add(xyPlane)
    center = adsk.core.Point3D.create(0, 0, 0)
    extrudes = headComp.features.extrudeFeatures
    bodySketch = sketches.add(xyPlane)
    bodySketch.sketchCurves.sketchCircles.addByCenterRadius(
        center, bodyDiameter/2)

    bodyProf = bodySketch.profiles[0]

    bodyExtInput = extrudes.createInput(
        bodyProf, adsk.fusion.FeatureOperations.JoinFeatureOperation)

    bodyExtInput.setAllExtent(
        adsk.fusion.ExtentDirections.NegativeExtentDirection)

    bodyExtInput.setDistanceExtent(
        False, adsk.core.ValueInput.createByReal(-1*bodyLength))
    bodyExt = extrudes.add(bodyExtInput)

    # create chamfer

    edgeCol = adsk.core.ObjectCollection.create()
    edges = bodyExt.endFaces[0].edges
    for edgeI in edges:
        edgeCol.add(edgeI)
    chamferFeats = headComp.features.chamferFeatures
    chamferInput = chamferFeats.createInput(edgeCol, True)
    chamferInput.setToEqualDistance(
        adsk.core.ValueInput.createByReal(chamferDistance))
    chamferFeats.add(chamferInput)

    edgeCol.clear()
    loops = bodyExt.sideFaces.item(0).edges.item(0).length
    for i in range(bodyExt.sideFaces.count):
        if bodyExt.sideFaces[i].geometry.surfaceType == 1:
            sideFace = bodyExt.sideFaces[i]

    threads = headComp.features.threadFeatures
    threadDataQuery = threads.threadDataQuery
    defaultThreadType = threadDataQuery.defaultMetricThreadType
    recommendData = threadDataQuery.recommendThreadData(bodyDiameter, False, defaultThreadType)
    if recommendData[0]:
             threadInfo = threads.createThreadInfo(
                 False, defaultThreadType, recommendData[1], recommendData[2])

    faces = adsk.core.ObjectCollection.create()

    faces.add(sideFace)
    threadInput = threads.createInput(faces, threadInfo)
    threads.add(threadInput)

    # edgeLoop = None
    # for edgeLoop in loops:
    #         ui.messageBox(str(edgeLoop))
    #         # since there two edgeloops in the start face of head, one consists of one circle edge while the other six edges
    #         if (len(edgeLoop.edges) == 1):
    #             break

    # edgeCol.add(edgeLoop.edges[0])
    return headComp,loops

