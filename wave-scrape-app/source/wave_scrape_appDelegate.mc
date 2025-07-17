import Toybox.WatchUi;
import Toybox.System;
import Toybox.Application;
import Toybox.Lang;

class wave_scrape_appDelegate extends WatchUi.BehaviorDelegate {
    
    private var _view as wave_scrape_appView;
    
    function initialize(view as wave_scrape_appView) {
        BehaviorDelegate.initialize();
        _view = view;
    }
    
    function onKey(keyEvent as WatchUi.KeyEvent) as Boolean {
        var key = keyEvent.getKey();
        
        if (key == WatchUi.KEY_UP) {
            _view.previousView();
            return true;
        } else if (key == WatchUi.KEY_DOWN) {
            _view.nextView();
            return true;
        } else if (key == WatchUi.KEY_ENTER) {
            // Refresh data on enter
            _view.requestWaveData();
            return true;
        }
        
        return false;
    }
    
    function onTap(clickEvent as WatchUi.ClickEvent) as Boolean {
        // Navigate on taps too
        _view.nextView();
        return true;
    }
}