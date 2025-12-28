import time
import gpiozero
import importlib
import logging
import sys

from display.abstract_display import AbstractDisplay
from PIL import Image
from pathlib import Path
from plugins.plugin_registry import get_plugin_instance

logger = logging.getLogger(__name__)

class WaveshareDisplay(AbstractDisplay):
    """
    Handles Waveshare e-paper display dynamically based on device type.

    This class loads the appropriate display driver dynamically based on the 
    `display_type` specified in the device configuration, allowing support for 
    multiple Waveshare EPD models.  

    The module drivers are in display.waveshare_epd.
    """

    def initialize_display(self):
        
        """
        Initializes the Waveshare display device.

        Retrieves the display type from the device configuration and dynamically 
        loads the corresponding Waveshare EPD driver from display.waveshare_epd.

        Raises:
            ValueError: If `display_type` is missing or the specified module is 
                        not found.
        """
        
        # Inside initialize_display(self):
        # Create manual CS controllers
        self.cs_pin_1 = gpiozero.LED(8)  # Physical Pin 24
        self.cs_pin_2 = gpiozero.LED(7)  # Physical Pin 26
        
        # Ensure both are HIGH (disabled) initially
        self.cs_pin_1.on()
        self.cs_pin_2.on()
        
        logger.info("Initializing Waveshare display")

        # get the device type which should be the model number of the device.
        display_type = self.device_config.get_config("display_type")  
        
        if not display_type:
            raise ValueError("Waveshare driver but 'display_type' not specified in configuration.")

        # Ensure the waveshare_epd directory is in path for relative imports
        epd_dir = Path(__file__).parent / "waveshare_epd"
        if str(epd_dir) not in sys.path:
            sys.path.insert(0, str(epd_dir))

        # Dynamically load the specific EPD model (e.g., epd7in3e)
        module_name = f"display.waveshare_epd.{display_type}" 
        self.epd_module = importlib.import_module(module_name)
        
        # We don't initialize self.epd_display here yet, 
        # because we need to set pins per-screen in display_image           
    def select_display(self, rst, dc, cs, busy):
                
        from display.waveshare_epd import epdconfig
        # epdconfig.RaspberryPi.CS_PIN = -1
        
        # 1. Cleanup existing GPIO pins to avoid "Pin in use" errors
        if hasattr(epdconfig, 'implementation') and epdconfig.implementation is not None:
            try:
                # This calls module_exit(cleanup=True) which closes gpiozero objects
                epdconfig.implementation.module_exit(cleanup=True)
            except Exception as e:
                logger.info(f"Cleanup info: {e}")

        # 2. Update the CLASS variables in RaspberryPi before creating the instance
        # This is necessary because epdconfig.RaspberryPi uses these to init gpiozero
        epdconfig.RaspberryPi.RST_PIN = rst
        epdconfig.RaspberryPi.DC_PIN = dc
        epdconfig.RaspberryPi.CS_PIN = -1 
        epdconfig.RaspberryPi.BUSY_PIN = busy
        
        # 3. Re-instantiate the hardware implementation with the new pin mapping
        epdconfig.implementation = epdconfig.RaspberryPi()
        
        # 4. Re-bind the module-level functions so epd7in3e.py uses the new implementation
        for func in [x for x in dir(epdconfig.implementation) if not x.startswith('_')]:
            setattr(epdconfig, func, getattr(epdconfig.implementation, func))

        # 5. Refresh the EPD object so it picks up the new pin values from epdconfig
        self.epd_display = self.epd_module.EPD()                  
        logger.info(
            f"Display re-instantiated with Pins: "
            f"MOSI={epdconfig.MOSI_PIN}, SCLK={epdconfig.SCLK_PIN}, "
            f"RST={epdconfig.RST_PIN}, DC={epdconfig.DC_PIN}, "
            f"CS={epdconfig.CS_PIN}, BUSY={epdconfig.BUSY_PIN}"
        )
        epdconfig.digital_write(epdconfig.RST_PIN, 1)
        time.sleep(0.1)
        epdconfig.digital_write(epdconfig.RST_PIN, 0)
        time.sleep(0.1)
        epdconfig.digital_write(epdconfig.RST_PIN, 1)
        time.sleep(0.1)

    def display_image(self, image, screen, image_settings=[]):
        
        """
        Displays an image on the Waveshare display.

        The image has been processed by adjusting orientation, resizing, and converting it
        into the buffer format required for e-paper rendering.

        Args:
            image (PIL.Image): The image to be displayed.
            image_settings (list, optional): Additional settings to modify image rendering.

        Raises:
            ValueError: If no image is provided.
        """

        if screen == 1:
            self.select_display(rst=17, dc=25, cs=8, busy=24)
            active_cs = self.cs_pin_1
        else:
            self.select_display(rst=27, dc=22, cs=7, busy=23)
            active_cs = self.cs_pin_2
        
        logger.info(f"Activating CS for screen {screen}")
        
        # MANUALLY ENABLE THE DISPLAY
        active_cs.off() # Pulls the pin LOW
        time.sleep(.1)
        
        
        try:
            self.epd_display.init()
            self.epd_display.Clear()
            self.epd_display.display(self.epd_display.getbuffer(image))
            self.epd_display.sleep()
        finally:
            # MANUALLY DISABLE THE DISPLAY
            active_cs.on() # Pulls the pin HIGH       