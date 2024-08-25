(function () {
  htmx.onLoad(() => {
    /*
    NOTE: this is not the best way to deal with this. Ideally
    it should be JS in the callback from the AJAX request that
    adds the element to the dom.
    */
    htmx.findAll(".toast").forEach((element) => {
      if (element.classList.contains('hide')) {
        // Remove hidden toasts from the dom
        element.remove();
      } else {
        // And show any new ones
        let toast = new bootstrap.Toast(element);
        toast.show()
      }
    });
  });
})();
