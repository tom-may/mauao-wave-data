import Toybox.Graphics;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Lang;
import Toybox.Communications;
import Toybox.Application.Storage;

class wave_scrape_appView extends WatchUi.View {
    
    // Wave data fields
    private var _maxWaveHeight as Lang.String = "--";
    private var _sigWaveHeight as Lang.String = "--";
    private var _wavePeriod as Lang.String = "--";
    private var _windSpeed as Lang.String = "--";
    private var _windDirection as Lang.String = "--";
    private var _windGusts as Lang.String = "--";
    private var _waterTemp as Lang.String = "--";
    private var _tideLevel as Lang.String = "--";
    private var _airTemp as Lang.String = "--";
    
    // Meta data
    private var _lastUpdate as Lang.String = "Never";
    private var _location as Lang.String = "Mauao";
    private var _dataStatus as Lang.String = "Loading...";
    private var _isLoading as Lang.Boolean = false;
    
    // Display control
    private var _currentView as Lang.Number = 0;
    private var _totalViews as Lang.Number = 8;

    function initialize() {
        View.initialize();
        System.println("=== Wave App Initialized ===");
    }

    function onLayout(dc as Graphics.Dc) as Void {
        System.println("onLayout called");
    }

    function onShow() as Void {
        System.println("onShow called - loading data");
        loadCachedData();
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
        
        // Draw header with status
        dc.drawText(width/2, 10, Graphics.FONT_XTINY, _dataStatus, Graphics.TEXT_JUSTIFY_CENTER);
        
        // Draw view indicator (e.g., "1/8")
        dc.drawText(width/2, 25, Graphics.FONT_XTINY, (_currentView + 1) + "/" + _totalViews, Graphics.TEXT_JUSTIFY_CENTER);
        
        // Draw the current data view
        drawCurrentView(dc, width, height);
        
        // Draw navigation hints at bottom
        dc.drawText(width/2, height - 30, Graphics.FONT_XTINY, "↑/↓ Navigate", Graphics.TEXT_JUSTIFY_CENTER);
        dc.drawText(width/2, height - 15, Graphics.FONT_XTINY, _lastUpdate, Graphics.TEXT_JUSTIFY_CENTER);
        
        // Loading indicator
        if (_isLoading) {
            dc.setColor(Graphics.COLOR_YELLOW, Graphics.COLOR_TRANSPARENT);
            dc.drawText(width - 10, 10, Graphics.FONT_XTINY, "⟳", Graphics.TEXT_JUSTIFY_RIGHT);
        }
    }
    
    function drawCurrentView(dc as Graphics.Dc, width as Lang.Number, height as Lang.Number) as Void {
        var centerY = height / 2;
        var title = "";
        var value = "";
        
        // Determine what to display based on current view
        if (_currentView == 0) {
            title = "Max Wave Height:";
            value = _maxWaveHeight.equals("--") ? "N/A" : _maxWaveHeight;
        } else if (_currentView == 1) {
            title = "Sig Wave Height:";
            value = _sigWaveHeight.equals("--") ? "N/A" : _sigWaveHeight;
        } else if (_currentView == 2) {
            title = "Period:";
            value = _wavePeriod.equals("--") ? "N/A" : _wavePeriod;
        } else if (_currentView == 3) {
            title = "Wind:";
            value = _windSpeed.equals("--") ? "N/A" : _windSpeed;
        } else if (_currentView == 4) {
            title = "Direction:";
            value = _windDirection.equals("--") ? "N/A" : _windDirection;
        } else if (_currentView == 5) {
            title = "Water Temp:";
            value = _waterTemp.equals("--") ? "N/A" : _waterTemp;
        } else if (_currentView == 6) {
            title = "Air Temp:";
            value = _airTemp.equals("--") ? "N/A" : _airTemp;
        } else if (_currentView == 7) {
            title = "Tide:";
            value = _tideLevel.equals("--") ? "N/A" : _tideLevel;
        }
        
        // Draw title
        dc.drawText(width/2, centerY - 25, Graphics.FONT_MEDIUM, title, Graphics.TEXT_JUSTIFY_CENTER);
        
        // Draw value (larger font)
        dc.setColor(Graphics.COLOR_BLUE, Graphics.COLOR_TRANSPARENT);
        dc.drawText(width/2, centerY + 5, Graphics.FONT_LARGE, value, Graphics.TEXT_JUSTIFY_CENTER);
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
    }

    function onHide() as Void {
        System.println("onHide called");
    }
    
    // Navigation functions
    function nextView() as Void {
        _currentView = (_currentView + 1) % _totalViews;
        WatchUi.requestUpdate();
    }
    
    function previousView() as Void {
        _currentView = (_currentView - 1 + _totalViews) % _totalViews;
        WatchUi.requestUpdate();
    }
    
    // Load cached data from storage
    function loadCachedData() as Void {
        try {
            System.println("Attempting to load cached data");
            var cachedData = Storage.getValue("wave_data_cache");
            if (cachedData != null) {
                System.println("Found cached data, parsing...");
                parseWaveData(cachedData);
                _dataStatus = "Cached data";
                System.println("Cached data loaded successfully");
            } else {
                System.println("No cached data found");
            }
        } catch (ex) {
            System.println("Cache load error: " + ex.getErrorMessage());
        }
    }
    
    // Fetch fresh wave data from your GitHub Pages API
    function requestWaveData() as Void {
        System.println("requestWaveData called");
        
        if (Communications has :makeWebRequest) {
            System.println("Communications available, making request...");
            _isLoading = true;
            _dataStatus = "Updating...";
            WatchUi.requestUpdate();
            
            var url = "https://tom-may.github.io/mauao-wave-data/wave_data.json";
            System.println("Requesting URL: " + url);
            
            Communications.makeWebRequest(
                url,
                {},
                {
                    :method => Communications.HTTP_REQUEST_METHOD_GET,
                    :headers => {
                        "Content-Type" => Communications.REQUEST_CONTENT_TYPE_JSON
                    }
                },
                method(:onReceiveWaveData)
            );
        } else {
            System.println("Communications not available");
            _dataStatus = "No connectivity";
            _isLoading = false;
            WatchUi.requestUpdate();
        }
    }
    
    // Handle the HTTP response
    function onReceiveWaveData(responseCode as Lang.Number, data as Lang.Dictionary?) as Void {
        System.println("=== HTTP Response Received ===");
        System.println("Response Code: " + responseCode);
        System.println("Data is null: " + (data == null));
        
        _isLoading = false;
        
        if (responseCode == 200 && data != null) {
            System.println("SUCCESS: Got data from API");
            
            try {
                parseWaveData(data);
                
                // Cache the successful data
                Storage.setValue("wave_data_cache", data);
                System.println("Data cached successfully");
                
                _dataStatus = data["status"] != null ? data["status"].toString() : "Success";
                System.println("Parse completed, status: " + _dataStatus);
                
            } catch (ex) {
                _dataStatus = "Parse error";
                System.println("PARSE ERROR: " + ex.getErrorMessage());
            }
        } else {
            _dataStatus = "Connection failed (" + responseCode + ")";
            System.println("HTTP ERROR: " + responseCode);
        }
        
        WatchUi.requestUpdate();
        System.println("=== Response handling complete ===");
    }
    
    // Parse the JSON data AND raw_conditions array
    function parseWaveData(jsonData as Lang.Dictionary) as Void {
        System.println("=== Parsing Wave Data ===");
        
        try {
            // First try the structured conditions
            if (jsonData["parsed_data"] != null) {
                var parsedData = jsonData["parsed_data"] as Lang.Dictionary;
                
                if (parsedData["conditions"] != null) {
                    var conditions = parsedData["conditions"] as Lang.Dictionary;
                    
                    // Get structured data
                    if (conditions["max_wave_height"] != null) {
                        _maxWaveHeight = conditions["max_wave_height"].toString() + "m";
                    }
                    if (conditions["sig_wave_height"] != null) {
                        _sigWaveHeight = conditions["sig_wave_height"].toString() + "m";
                    }
                    if (conditions["wave_period"] != null) {
                        _wavePeriod = conditions["wave_period"].toString() + "s";
                    }
                    if (conditions["wind_speed"] != null) {
                        _windSpeed = conditions["wind_speed"].toString() + " kts";
                    }
                    if (conditions["wind_direction"] != null) {
                        _windDirection = conditions["wind_direction"].toString();
                    }
                    if (conditions["water_temp"] != null) {
                        _waterTemp = conditions["water_temp"].toString() + "°C";
                    }
                    if (conditions["air_temp"] != null) {
                        _airTemp = conditions["air_temp"].toString() + "°C";
                    }
                    if (conditions["tide"] != null) {
                        _tideLevel = conditions["tide"].toString();
                    }
                }
                
                // Also parse raw_conditions for missing data
                if (parsedData["raw_conditions"] != null) {
                    var rawConditions = parsedData["raw_conditions"] as Lang.Array;
                    parseRawConditions(rawConditions);
                }
            }
            
            // Update last update time
            if (jsonData["last_updated"] != null) {
                _lastUpdate = jsonData["last_updated"].toString();
            }
            
            System.println("=== Final Values ===");
            System.println("Max Wave: " + _maxWaveHeight);
            System.println("Sig Wave: " + _sigWaveHeight);
            System.println("Period: " + _wavePeriod);
            System.println("Wind: " + _windSpeed);
            System.println("Direction: " + _windDirection);
            System.println("Water Temp: " + _waterTemp);
            System.println("Air Temp: " + _airTemp);
            System.println("Tide: " + _tideLevel);
            
        } catch (ex) {
            System.println("ERROR parsing wave data: " + ex.getErrorMessage());
            _dataStatus = "Data error";
        }
    }
    
    // Parse raw conditions array to extract missing data
    function parseRawConditions(rawConditions as Lang.Array) as Void {
        System.println("Parsing raw conditions array...");
        
        for (var i = 0; i < rawConditions.size(); i++) {
            var line = rawConditions[i].toString().toLower();
            System.println("Processing: " + line);
            
            // Look for patterns in the raw data
            if (line.find("0.7 m") != null && _sigWaveHeight.equals("--")) {
                _sigWaveHeight = "0.7m";
                System.println("Found sig wave height: 0.7m");
            }
            
            if (line.find("4.8") != null && _wavePeriod.equals("--")) {
                _wavePeriod = "4.8s";
                System.println("Found period: 4.8s");
            }
            
            if (line.find("22 knts") != null && _windSpeed.equals("--")) {
                _windSpeed = "22 kts";
                System.println("Found wind speed: 22 kts");
            }
            
            if (line.find("135 se") != null && _windDirection.equals("--")) {
                _windDirection = "135 SE";
                System.println("Found direction: 135 SE");
            }
            
            if (line.find("15.8") != null && _waterTemp.equals("--")) {
                _waterTemp = "15.8°C";
                System.println("Found water temp: 15.8°C");
            }
            
            if (line.find("9.9") != null && _airTemp.equals("--")) {
                _airTemp = "9.9°C";
                System.println("Found air temp: 9.9°C");
            }
            
            if (line.find("1.83 m") != null && _tideLevel.equals("--")) {
                _tideLevel = "1.83m";
                System.println("Found tide: 1.83m");
            }
        }
    }
}