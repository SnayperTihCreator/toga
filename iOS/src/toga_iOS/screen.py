from rubicon.objc import Block, objc_id

from toga.screen import Screen as ScreenInterface
from toga_iOS.libs import UIGraphicsImageRenderer, UIImage


class Screen:
    _instances = {}

    def __new__(cls, native):
        if native in cls._instances:
            return cls._instances[native]
        else:
            instance = super().__new__(cls)
            instance.interface = ScreenInterface(_impl=instance)
            instance.native = native
            cls._instances[native] = instance
            return instance

    def get_name(self):
        # Return a dummy name as UIScreen object has no name related attributes.
        return "iOS Screen"

    def get_origin(self):
        return (0, 0)

    def get_size(self):
        return int(self.native.nativeBounds.size.width), int(
            self.native.nativeBounds.size.height
        )

    def get_image_data(self):
        ui_view = self.native.snapshotViewAfterScreenUpdates_(True)
        renderer = UIGraphicsImageRenderer.alloc().initWithSize(ui_view.bounds.size)

        def render(context):
            ui_view.drawViewHierarchyInRect(ui_view.bounds, afterScreenUpdates=True)

        ui_image = UIImage.imageWithData(
            renderer.PNGDataWithActions(Block(render, None, objc_id))
        )
        return ui_image
