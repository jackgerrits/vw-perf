function debounce(fn, delay) {
  var timer = null;
  return function () {
      var context = this,
          args = arguments,
          evt = d3.event;
      //we get the D3 event here
      clearTimeout(timer);
      timer = setTimeout(function () {
          d3.event = evt;
          //and use the reference here
          fn.apply(context, args);
      }, delay);
  };
}