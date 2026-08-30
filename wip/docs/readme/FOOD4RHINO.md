# Food4Rhino listing (not published yet)

LoopFlow Rhino to Blender Sync pushes models, cameras, and light points one way from Rhino 8 into Blender. It exports a clean model, writes the view and point positions, and updates on the Blender side.

Typical flow: model in Rhino as you already do, then publish the model, a selection, the camera, or lights when you need them. Blender reads the exchange files from the same project folder. When the model updates, materials you already tuned under the same names can stay. Each channel is independent; you do not have to run them all at once.

The aim is to keep Rhino's design freedom, while cutting the repeat work of rebuilding the render scene after every model change.

Install from Rhino's Package Manager (search **loopflow Rhino to Blender Sync**). On the Blender side, use the zip the package copies into Documents\LoopFlow, and install it with Add-ons → Install from Disk.

Do not mix old 2.x toolbars, packages, or the Blender add-on with this version in the same project.

Requirements: Rhino 8 (Windows 10/11), Blender 5.2.1 (development target). UI: English. Documentation: English / Traditional Chinese.
