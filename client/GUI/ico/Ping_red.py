from GUI.helper.SvgToPng import SvgToPng


class PingRed(SvgToPng):
    '''
    example use
    from GUI.Ping_red import Ping_red
    self.lbl_info_ico.setPixmap(Ping_red().get_pixmap())
    '''

    def __init__(self):
        super().__init__()
        self.src = '''<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
            <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="150px" height="150px" style="shape-rendering:geometricPrecision; text-rendering:geometricPrecision; image-rendering:optimizeQuality; fill-rule:evenodd; clip-rule:evenodd" xmlns:xlink="http://www.w3.org/1999/xlink">
            <g><path style="opacity:1" fill="#aa0100" d="M 61.5,7.5 C 92.7001,3.52326 116.867,14.5233 134,40.5C 142.12,55.5181 144.787,71.5181 142,88.5C 134.842,116.991 117.009,134.825 88.5,142C 53.2926,146.483 27.7926,132.983 12,101.5C 0.745922,69.0041 8.24592,41.8374 34.5,20C 42.8204,14.1704 51.8204,10.0037 61.5,7.5 Z"/></g>
            </svg>
        '''

