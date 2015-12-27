var file_content = null;
var file_type = null;

var get_file = function(file_url, callback){
    var content;
    $.ajax({
        url: file_url,
        type: "GET",
        dataType: "binary",
        responseType: "arraybuffer",
        processData: false,
        async:false,
        success: function(result, a, xhr){
			var data = new Uint8Array(result);
			var arr = new Array();
			for(var i = 0; i != data.length; ++i) arr[i] = String.fromCharCode(data[i]);
			file_content = arr.join("");
            file_type = xhr.getResponseHeader('content-type');
        },
        error: function (xhr, ajaxOptions, thrownError) {
            console.log(xhr.status);
            console.log(thrownError);
        }
    });
};

var xls_open = function(url){
  /* set up XMLHttpRequest */
var oReq = new XMLHttpRequest();
oReq.open("GET", url, true);
oReq.responseType = "arraybuffer";

oReq.onload = function(e) {
  var arraybuffer = oReq.response;

  /* convert data to binary string */
  var data = new Uint8Array(arraybuffer);
  var arr = new Array();
  for(var i = 0; i != data.length; ++i) arr[i] = String.fromCharCode(data[i]);
  var bstr = arr.join("");

  /* Call XLSX */
  var workbook = XLSX.read(bstr, {type:"binary"});
  console.log(workbook);
  /* DO SOMETHING WITH workbook HERE */
}

oReq.send();
}
