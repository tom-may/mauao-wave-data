import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;

class wave_scrape_appApp extends Application.AppBase {

    function initialize() {
        AppBase.initialize();
    }

    function onStart(state as Dictionary?) as Void {
    }

    function onStop(state as Dictionary?) as Void {
    }

    function getInitialView() as [Views] or [Views, InputDelegates] {
        var view = new wave_scrape_appView();
        var delegate = new wave_scrape_appDelegate(view);
        return [ view, delegate ];
    }
}

function getApp() as wave_scrape_appApp {
    return Application.getApp() as wave_scrape_appApp;
}