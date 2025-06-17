import Toybox.Graphics;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Lang;

class wave_scrape_appView extends WatchUi.View {
    
    private var _waveHeight as Lang.String = "--";
    private var _wavePeriod as Lang.String = "--";
    private var _lastUpdate as Lang.String = "Never";

    function initialize() {
        View.initialize();
    }

    function onLayout(dc as Graphics.Dc) as Void {
        // Simple layout without resource dependency for now
    }

    function onShow() as Void {
        // Request initial wave data update
        requestWaveData();
    }

    function onUpdate(dc as Graphics.Dc) as Void {
        // Clear the screen
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();
        
        // Set text color
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
        
        var width = dc.getWidth();
        var height = dc.getHeight();
        
        // Draw title
        dc.drawText(width/2, 20, Graphics.FONT_MEDIUM, "Wave Data", Graphics.TEXT_JUSTIFY_CENTER);
        
        // Draw wave height
        dc.drawText(width/2, height/2 - 40, Graphics.FONT_LARGE, 
                   "Height: " + _waveHeight + "m", Graphics.TEXT_JUSTIFY_CENTER);
        
        // Draw wave period
        dc.drawText(width/2, height/2, Graphics.FONT_MEDIUM, 
                   "Period: " + _wavePeriod + "s", Graphics.TEXT_JUSTIFY_CENTER);
        
        // Draw last update time
        dc.drawText(width/2, height - 40, Graphics.FONT_SMALL, 
                   "Updated: " + _lastUpdate, Graphics.TEXT_JUSTIFY_CENTER);
    }

    function onHide() as Void {
    }
    
    // Simulate wave data request
    function requestWaveData() as Void {
        _waveHeight = "1.2";
        _wavePeriod = "8";
        var clockTime = System.getClockTime();
        _lastUpdate = clockTime.hour.format("%02d") + ":" + 
                     clockTime.min.format("%02d");
        
        WatchUi.requestUpdate();
    }
}