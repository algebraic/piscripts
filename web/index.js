$(function() {

  
  /* help content */
  $("h6").click(function() {
    var $this = $(this);
    var heading = $this.text();
    var id = $this.parents("section").attr("class");

    $.toast({
      heading: heading,
      text: $("#help-" + id).html(),
      hideAfter: false,
      showHideTransition: 'slide',
      icon: 'info',
      position: 'bottom-right',
    });
  });

  // rehide everything prior to load
  $(".container, .nav-item").hide();
    handleClientLoad();


/* zj: stuff above here is new and definitely being used */

  // save
  $("#save").click(function() {
    
    // check if google drive is connected
    var google = gapi.auth2.getAuthInstance().isSignedIn.get();
    
    var d = new Date();
    var strDate = d.getMonth()+1 + "/" + d.getDate() + "/" + d.getFullYear();
    var name = "item_" + $("[name=case_name]").val() + " " + strDate;
    var strName = name;
    
    var data = null;
    // grab data from local storage
    data = JSON.parse(localStorage.getItem("sort_config_data"));
    
    var jsonObj = {
      "data": [{
        name: name,
        form: $("form").serializeFormJSON()
      }]
    }
    
    if (data === null) {
      // new, just save to local storage
      console.log("saving to local storage...");
      data = jsonObj;
      localStorage.setItem("sort_config_data", JSON.stringify(jsonObj));
    } else {
      // existing stuff, append new item
      data.data.push(jsonObj.data[0]);
      localStorage.setItem("sort_config_data", JSON.stringify(data));
    }
    
    if (google) {
      // check if there's a savedfileid
      var existingFile = false;
      if (data["savedfileid"]) {
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
  });
  
  // collapse navbar when clicking off it
  $(document).on("click", "*", function(event) {
    var clickover = $(event.target);
    var $navbar = $(".navbar-collapse");
    var _opened = $navbar.hasClass("show");
    var nav = (clickover.hasClass("navbar") || (clickover.parents(".navbar").length > 0));
    if (!nav) {
      $navbar.collapse('hide');
    }
  });


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
    console.warn("getSavedFile()");
    var savedfileid = null;
    gapi.client.drive.files.list({
      // 'pageSize': 0, // removed pagesize, dumb
      'fields': "nextPageToken, files(id, name)"
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
                if (!jsonobj.savedfileid) {
                  jsonobj.savedfileid = savedfileid;
                  // drop into local storage
                  localStorage.setItem("sort_config_data", JSON.stringify(jsonobj));
                }
                $.each(jsonobj.config, function(key, value) { 
                  var $ctrl = $('#' + key);
                  // console.info("key = " + key + " -- " + "value = " + value);
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
                $.each(jsonobj.nameReplace, function(key, value) {
                  $("#nameReplace tbody").append("<tr><td contenteditable='true'>" + key + "</td><td contenteditable='true'>" + value + "</td></tr>");
                });
                // insert delete buttons
                $("tr").each(function() {
                  $("td:eq(1)", this).after("<td><i class='fas fa-times delete'></i></td>");
                });
                $(document).on("click", ".delete", function() {
                  console.info("delete");
                  $(this).parents("tr").remove();
                });

                // table editing stuff
                $("td").keypress(function(e) {
                  if (e.which == 13) {
                    e.preventDefault();
                    $(this).blur();
                  }
                }).blur(function(e) {
                  e.currentTarget.innerText = $.trim(e.currentTarget.innerText);
                });
                
              });
            }
        });
      } else {
        // no file in google drive
        console.log("no file exists in drive");
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
            console.info('yay, callback');
            console.log(file)
          };
            
          request.execute(callback);
        }
    }  
