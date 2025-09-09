from GUI.helper.SvgToPng import SvgToPng


class btn_ico_ok(SvgToPng):
    '''
    example use
    from GUI.btn_ico_ok import btn_ico_ok
    self.lbl_info_ico.setPixmap(btn_ico_ok().get_pixmap())
    '''

    def __init__(self):
        super().__init__()
        self.src = '''<?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
            <svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="153px" height="153px" style="shape-rendering:geometricPrecision; text-rendering:geometricPrecision; image-rendering:optimizeQuality; fill-rule:evenodd; clip-rule:evenodd" xmlns:xlink="http://www.w3.org/1999/xlink">
            <g><path style="opacity:0.171" fill="#001100" d="M 109.5,23.5 C 135.624,22.4806 145.457,34.8139 139,60.5C 138.333,61.8333 137.667,63.1667 137,64.5C 118.507,85.326 99.6734,105.826 80.5,126C 69.6952,129.561 59.0285,129.228 48.5,125C 36.9602,112.462 25.7936,99.629 15,86.5C 8.07249,54.4278 20.5725,42.2612 52.5,50C 56.9573,54.4461 61.2907,58.9461 65.5,63.5C 76.8392,51.9937 87.8392,40.1604 98.5,28C 102.053,25.8792 105.72,24.3792 109.5,23.5 Z"/></g>
            <g><path style="opacity:1" fill="#00bf00" d="M 110.5,34.5 C 121.883,32.5622 128.55,37.2289 130.5,48.5C 130.534,51.4334 129.701,54.1 128,56.5C 109.868,76.9666 91.3685,97.1333 72.5,117C 64.9693,119.905 58.4693,118.405 53,112.5C 43.7081,100.873 34.0415,89.5393 24,78.5C 22.1156,62.8563 28.949,56.3563 44.5,59C 51.3446,66.6768 58.3446,74.1768 65.5,81.5C 80.1846,65.4831 95.1846,49.8165 110.5,34.5 Z"/></g>
            </svg>
        '''

