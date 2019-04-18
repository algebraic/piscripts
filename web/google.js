/*
GOOGLE DRIVE API STUFF
*/

// from Google Developer Console, https://console.developers.google.com/apis/credentials?project=imposing-fin-196415
var CLIENT_ID = '646751083447-2uv66stq260tabe193nhsp3e263sipe4.apps.googleusercontent.com';
var API_KEY = 'AIzaSyB-1yrZtwg_39EjmeEh4V1jwgpa54oAw-0';

// Array of API discovery doc URLs for APIs used by the quickstart
var DISCOVERY_DOCS = ["https://www.googleapis.com/discovery/v1/apis/drive/v3/rest"];

// Authorization scopes required by the API; multiple scopes can be
// included, separated by spaces.
var SCOPES = 'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.appdata';


// load auth2 library & API client library
function handleClientLoad() {
    console.info("handleClientLoad()");
    gapi.load('client:auth2', initClient);
}

// Initialize API client library & sign-in state listeners
function initClient() {
    console.info("google initClient");
    // login/logout buttons
    const $authorizeButton = $("#drive_login");
    const $signoutButton = $("#drive_logout");

    gapi.client.init({
        apiKey: API_KEY,
        clientId: CLIENT_ID,
        discoveryDocs: DISCOVERY_DOCS,
        fetchBasicProfile: true,
        scope: SCOPES
    }).then(function () {
        console.info("in the 'then'");
        // listen for sign-in state changes
        gapi.auth2.getAuthInstance().isSignedIn.listen(updateSigninStatus);
        console.info("yay");
        // handle initial sign-in state
        var isSignedIn = gapi.auth2.getAuthInstance().isSignedIn.get();
        updateSigninStatus(isSignedIn);

        console.info("$authorizeButton: " + $authorizeButton.length);

        $authorizeButton.click(function(e) {
            console.info("sign in");
            handleAuthClick(e);
        });
        $signoutButton.click(function(e) {
            console.info("sign out");
            handleSignoutClick(e);
        });
    });
}

// called when login status changes to update UI appropriately - after a login, the API is called
function updateSigninStatus(isSignedIn) {
    console.info("updateSigninStatus()");
    var $authorizeButton = $(".drive_login");
    var $signoutButton = $(".drive_logout");
    var $buttons = $(".drive-buttons");

    console.info("signed in = " + isSignedIn);
    var guser = null;
    if (isSignedIn) {
        // get google user
        gapi.client.load('plus','v1', function(){
            var request = gapi.client.plus.people.get({
                'userId': 'me'
            });
            request.execute(function(resp) {
                guser = resp;
                console.log('Retrieved profile for:' + resp.displayName);
                $("#google-user").text(guser.displayName);
            });
        });
        
        // grab any saved entries
        getSavedFile();
        
        // button maneuvers
        $authorizeButton.hide();
        $signoutButton.show();
        $("div.container, .nav-item").show();
        $(".nav-link:first").click();
        $(".google-warning").remove();
    } else {
        $authorizeButton.show();
        $signoutButton.hide();
        $("body").append("<div class='google-warning'>Connect your Google account to save app data in Google Drive</div>");
        $("div.container, .nav-item").hide();

    }
    $buttons.removeClass("hide");
    $(".nav-link").eq(1).click();
}

// google drive login/logout
function handleAuthClick(event) {
    console.info("handleAuthClick()");
    options = new gapi.auth2.SigninOptionsBuilder();
    options.setPrompt('select_account');
    gapi.auth2.getAuthInstance().signIn(options);
}

function handleSignoutClick(event) {
    gapi.auth2.getAuthInstance().signOut();
}