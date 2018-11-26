function errorMsg(msg, error) {
  errorElement.innerHTML += '<p>' + msg + '</p>';
  if (typeof error !== 'undefined') {
    console.error(error);
  }
};

function send_data() {
  var handleSuccess = function(stream) {
    var context = new AudioContext();
    var input = context.createMediaStreamSource(stream);
    var processor = context.createScriptProcessor(1024, 1, 1);

    var connection = new WebSocket('ws://localhost:5000/audios');
    connection.onmessage = function(e) {
      var restart_url = "http://localhost:5000/restart?result=" + e.data;
      location.href = restart_url;
    };

    input.connect(processor);
    processor.connect(context.destination);

    processor.onaudioprocess = function(e) {
      var audio_data = e.inputBuffer.getChannelData(0);
      connection.send(audio_data.buffer);
    };
  };

  var handleError = function(error) {
    if (error.name === 'PermissionDeniedError') {
        errorMsg('Permissions have not been granted to use your microphone.', error);
    } else {
        errorMsg('getUserMedia error: ' + error.name, error);
    }
  };

  navigator.mediaDevices.getUserMedia({ audio: true, video: false })
      .then(handleSuccess)
      .catch(handleError);
};

send_data();
