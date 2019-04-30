$(function() {
  
  /* help content */
  $("h5").click(function() {
    var $this = $(this);
    var heading = $this.text();
    var id = $this.parents("section").attr("class");
    var text = $("#help-" + id).html();
    showHelp(heading, text);
  });
  $("h4.help").click(function() {
    var $this = $(this);
    var heading = $this.text();
    var id = $this.parents("section").attr("class");
    var text = $("#help-" + id).html();
    showHelp(heading, text);
  });

  // rehide everything prior to load
  $(".container, .nav-item").hide();
  handleClientLoad();

  // save
  $("#save").click(function() {
    // button stuff
    $(this).prop("disabled", true);
    $(".save-button .fa-save").addClass("hide");

    // close navbar if open
    $('.navbar-collapse').collapse('hide');

    // check if google drive is connected
    var google = gapi.auth2.getAuthInstance().isSignedIn.get();
    
    var d = new Date();
    var strDate = d.getMonth()+1 + "/" + d.getDate() + "/" + d.getFullYear();
    
    var data = null;
    // grab data from local storage
    data = JSON.parse(localStorage.getItem("sort_config_data"));
    
    var jsonObj = {
      "config" : {}, 
      "nameReplace" : {}, 
      "forceId" : {}, 
      "advanced" : { 
        "notifications" : {},
        "offset" : {
          "episode" : {},
          "season" : {}
        },
        "triggercmd" : {
          "token" : {}
        }
      },
      "savedfileid":""
    }

    if (data && data["savedfileid"]) {
      jsonObj["savedfileid"] = data["savedfileid"];
    }

    // config section
    $("section", ".section-basic").each(function() {
      var $section = $(this);
      $("input, select", $section).each(function() {
        var $input = $(this);
        var id = $input.attr("id");
        var type = $input.prop("type");
        var value = $input.val();
        if (type == "checkbox") {
          if ($input.prop("checked")) {
            value = true;
          } else {
            value = false;
          }
        }
        jsonObj["config"][id] = value;
      });
    });

    // force name/id sections
    $("#nameReplace, #forceId").each(function() {
      var $table = $(this);
      var id = $table.attr("id");
      $("tbody tr", $table).each(function() {
        var $row = $(this);
        jsonObj[id][$("td:eq(0)", $row).text()] = $("td:eq(1)", $row).text();
      });
    });
    // shows_list & mediaExts, fewer fields so handle separately
    var showlist = [];
    $("tbody tr", "table#shows_list").each(function() {
      var $row = $(this);
      showlist.push($("td:eq(0)", $row).text());
    });
    jsonObj["advanced"]["notifications"]["shows_list"] = showlist;
    // media extensions
    var extlist = [];
    $("tbody tr", "table#mediaExts").each(function() {
      var $row = $(this);
      extlist.push($("td:eq(0)", $row).text());
    });
    jsonObj["config"]["mediaExts"] = extlist;
    // offsets
    $("table", "section.offsets").each(function() {
      var $table = $(this);
      $("tbody tr", $table).each(function() {
        var $row = $(this);
        jsonObj["advanced"]["offset"][$table.attr("id")][$("td:eq(0)", $row).text()] = $("td:eq(1)", $row).text();
      });
    });

    // advanced section
    $("section", ".section-advanced").each(function() {
      var $section = $(this);
      $("input, select, textarea", $section).each(function() {
        var $input = $(this);
        var id = $input.attr("id");
        var type = $input.prop("type");
        var value = $input.val();
        if (type == "checkbox") {
          if ($input.prop("checked")) {
            value = true;
          } else {
            value = false;
          }
        }
        jsonObj["advanced"][$section.attr("class")][id] = value;
      });
    });

    localStorage.setItem("sort_config_data", JSON.stringify(jsonObj));
    if (google) {
      // check if there's a savedfileid
      var existingFile = false;
      if (jsonObj["savedfileid"]) {
        //zj: ^^ dying here, see wtf?
        existingFile = true;
      }
      saveFile(existingFile);
    }
    
  });

  // nav links, swap sections
  $(".nav-link").click(function() {
    var section = $(this).attr("id");
    $("div.container").hide();
    $("div.section-" + section).show();
    $('.navbar-collapse').collapse('hide');
  });
  
  // add new table row
  $(document).on("click", ".add-row", function() {
    var add = true;
    var $table = $(this).parents("table");
    $("tr:not(.add-row):last td:not(.delete-row)", $table).each(function() {
      var $this = $(this);
      if ($this.index() < 2 && $this.text().length == 0) {
        add = false;
        $this.focus();
        return false;
      }
    });
    if (add) {
      var row = "<tr><td contenteditable='true'></td><td contenteditable='true'></td><td class='delete-row'><i class='fas fa-times delete'></i></td></tr>";
      if ($table.hasClass("one-col")) {
        var row = "<tr><td contenteditable='true'></td><td class='delete-row'><i class='fas fa-times delete'></i></td></tr>";
      }
      $table.append(row);
      $("tr:not(.add-row):last td:first", $table).focus();
    }
  });

  // help toasts
  function showHelp(heading, text) {
    $.toast({
      heading: heading,
      text: text,
      hideAfter: false,
      showHideTransition: 'slide',
      icon: 'info',
      position: 'bottom-right',
    });
  }

  // convert form to json object
  $.fn.serializeFormJSON = function () {
    var o = {};
    var a = this.serializeArray();
    $.each(a, function () {
      if (o[this.name]) {
        if (!o[this.name].push) {
          o[this.name] = [o[this.name]];
        }
        o[this.name].push(this.value || '');
      } else {
        o[this.name] = this.value || '';
      }
    });
    return o;
  };
  

});

  
  function getSavedFile() {
    // look for an existing sort.config.json in drive, load if found
    var savedfileid = null;
    
    gapi.client.drive.files.list({
      'pageSize': 1000, // removed pagesize, dumb
      'fields': "nextPageToken, files(id, name)",
      'q':"name='sort.config.json'"
    }).then(function(response) {
      // search through filenames
      var files = response.result.files;
      if (files && files.length > 0) {
        for (var i = 0; i < files.length; i++) {
          if (files[i].name == "sort.config.json") {
            savedfileid = files[i].id;
          }
        }
      }
      
      if (savedfileid != null) {
        // set file query stuff
        var url = "https://www.googleapis.com/drive/v3/files/" + savedfileid + "?alt=media";
        var accessToken = gapi.auth.getToken().access_token;
        var setHeaders = new Headers();
        setHeaders.append('Authorization', 'Bearer ' + accessToken);
        setHeaders.append('Content-Type', "text/json");
        var setOptions = {
          method: 'GET',
          headers: setHeaders
        };
        // try to make fetch happen
        fetch(url, setOptions)
          .then(response => {
            if (response.ok) {
              var reader = response.body.getReader();
              var decoder = new TextDecoder();
              reader.read().then(function(result) {
                var data = {}
                data = decoder.decode(result.value, {
                  stream: !result.done
                });
                // append savedfileid if not there already
                var jsonobj = JSON.parse(data);

                jsonobj.savedfileid = savedfileid;
                // drop into local storage
                localStorage.setItem("sort_config_data", JSON.stringify(jsonobj));
                $("#savedfileid").val(savedfileid);

                $.each(jsonobj.config, function(key, value) { 
                  var $ctrl = $('#' + key);
                  if ($ctrl.prop("nodeName") == "TABLE") {
                    $.each(value, function(k, v) {
                      $("tbody", "#" + $ctrl.attr("id")).append("<tr><td contenteditable='true'>" + v + "</td></tr>");
                    });
                  } else {
                    switch($ctrl.attr("type")) {
                      case "radio" : case "checkbox":
                        if (value) {
                          $ctrl.attr("checked",true); 
                        }
                      break;
                      default:
                        $ctrl.val(value);
                    }
                  }
                });
                $.each(jsonobj.nameReplace, function(key, value) {
                  $("#nameReplace tbody").append("<tr><td contenteditable='true'>" + key + "</td><td contenteditable='true'>" + value + "</td></tr>");
                });
                $.each(jsonobj.forceId, function(key, value) {
                  $("#forceId tbody").append("<tr><td contenteditable='true'>" + key + "</td><td contenteditable='true'>" + value + "</td></tr>");
                });
                $.each(jsonobj.advanced.notifications, function(key, value) {
                  var $ctrl = $('#' + key);
                  if ($ctrl.prop("nodeName") == "TABLE") {
                    $.each(value, function(k, v) {
                      $("tbody", $ctrl).append("<tr><td contenteditable='true'>" + v + "</td></tr>");
                    });
                  } else {
                    switch($ctrl.attr("type")) {
                      case "radio" : case "checkbox":
                        if (value) {
                          $ctrl.attr("checked",true); 
                        }
                        break;
                      default:
                        $ctrl.val(value);
                    }
                  }
                });
                
                $.each(jsonobj.advanced.triggercmd, function(key, value) {
                  var $ctrl = $('#' + key);
                  switch($ctrl.attr("type")) {
                    case "radio" : case "checkbox":
                      if (value) {
                        $ctrl.attr("checked",true); 
                      }
                      break;
                    default:
                      $ctrl.val(value);
                  }
                });
                // triggercmd token for download config file bookmark token
                $("#token").val(jsonobj.advanced.triggercmd.token);

                $.each(jsonobj.advanced.offset, function(key, value) {
                  var $ctrl = $('#' + key);
                  $.each(value, function(k, v) {
                    $("tbody", $ctrl).append("<tr><td contenteditable='true'>" + k + "</td><td contenteditable='true'>" + v + "</td></tr>");
                  });
                });


                // init tablesorter
                $("table").tablesorter({ sortList: [[0,0]] });

                // insert delete buttons
                $("table").each(function() {
                  var $table = $(this);
                  var id = $table.attr("id");
                  var num = 1;
                  if (id == "shows_list" || id == "mediaExts") {
                    num = 0;
                  }
                  $("tr", $table).not(".add-row").each(function() {
                    $("td:eq(" + num + ")", this).after("<td class='delete-row'><i class='fas fa-times delete'></i></td>");
                  });
                });
                $(document).on("click", ".delete", function() {
                  $(this).parents("tr").remove();
                });

                // table editing stuff
                $(document).on("keypress", "td", function(e) {
                  if (e.which == 13) {
                    e.preventDefault();
                    $(this).blur();
                  }
                }).on("blur", "td", function(e) {
                  e.currentTarget.innerText = $.trim(e.currentTarget.innerText);
                });
                
              });
            }
        });
      } else {
        // no file in google drive
        console.log("no file exists in drive");
        $.toast({
          heading: "Config file not found",
          text: "No config file exists in Google Drive yet",
          hideAfter: false,
          showHideTransition: 'slide',
          icon: 'warning',
          position: 'bottom-right',
        });
      }

    });
  }

  function saveFile(existingFile) {
    // save new file to drive
    console.log("saving to google...");
    
    // construct json object
    var jsonObj = JSON.parse(localStorage.getItem("sort_config_data"));
    
    var jsonFile = new Blob([JSON.stringify(jsonObj)], {type : "text/json"});
    var boundary = '-------314159265358979323846';
    var delimiter = "\r\n--" + boundary + "\r\n";
    var close_delim = "\r\n--" + boundary + "--";
    var reader = new FileReader();
    reader.readAsBinaryString(jsonFile);
      reader.onload = function(e) {
        var contentType = jsonFile.type || 'application/octet-stream';
        var metadata = {
          'title': "sort.config.json",
          'mimeType': contentType
        };

        var base64Data = btoa(reader.result);
        var multipartRequestBody =
          delimiter +
          'Content-Type: application/json\r\n\r\n' +
          JSON.stringify(metadata) +
          delimiter +
          'Content-Type: ' + contentType + '\r\n' +
          'Content-Transfer-Encoding: base64\r\n' +
          '\r\n' +
          base64Data +
          close_delim;

          var path = '/upload/drive/v2/files/';
          var method = "POST";
          if (existingFile) {
            path = '/upload/drive/v2/files/' + jsonObj.savedfileid;
            method = "PUT";
          }
         
          var request = gapi.client.request({
            'path': path,
            'method': method,
            'params': {'uploadType': 'multipart', 'alt': 'json'},
            'headers': {
              'Content-Type': 'multipart/mixed; boundary="' + boundary + '"'
            },
            'body': multipartRequestBody});
        
          callback = function(file) {
            console.log(file);
            $.toast({
              heading: "Config Saved",
              text: "Your configuration file has been saved to Google Drive",
              showHideTransition: 'slide',
              icon: 'success',
              position: 'bottom-right',
            });
            $("#save").prop("disabled", false);
            // window.location.reload();

            if (jsonObj.advanced.triggercmd.autodownload) {
              runTriggerCMD(jsonObj.advanced.triggercmd.token);
            }
          };
            
          request.execute(callback);
        }
    }  

function runTriggerCMD(token) {
  $.get("https://www.triggercmd.com/trigger/bookmark?token=" + token, function(data,status) {
      switch($ctrl.attr("type")) {
        case "radio" : case "checkbox":
          if (value) {
            $ctrl.attr("checked",true); 
          }
          break;
        default:
          $ctrl.val(value);
      }
  }).fail(function() {
    // the triggercmd get fails in console with CORS errors but script does execute
    // alert("fail");
  }).always(function() {
    // alert("always");
    $.toast({
      heading: "TriggerCMD Command Sent",
      text: "Your TriggerCMD command has been executed",
      showHideTransition: 'slide',
      icon: 'success',
      position: 'bottom-right',
    });
  });
}