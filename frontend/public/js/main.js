requirejs.config({
  baseUrl: ".",
  paths: {
    knockout: "https://static.oracle.com/cdn/jet/v15.0.0/default/js/libs/knockout/knockout-3.5.1",
    jquery: "https://static.oracle.com/cdn/jet/v15.0.0/default/js/libs/jquery/jquery-3.6.0.min",
    ojs: "https://static.oracle.com/cdn/jet/v15.0.0/default/js/min",
    ojL10n: "https://static.oracle.com/cdn/jet/v15.0.0/default/js/ojL10n",
    ojtranslations:
      "https://static.oracle.com/cdn/jet/v15.0.0/default/js/resources",
    text: "https://static.oracle.com/cdn/jet/v15.0.0/default/js/libs/require/text",
    signals: "https://static.oracle.com/cdn/jet/v15.0.0/default/js/libs/js-signals/signals.min",
    ojdnd: "https://static.oracle.com/cdn/jet/v15.0.0/default/js/libs/dnd-polyfill/dnd-polyfill-1.0.2.min",
  },
  shim: {
    jquery: {
      exports: ["jQuery", "$"],
    },
  },
});

require(
  ["ojs/ojbootstrap", "knockout", "ojs/ojmodule-element-utils", "ojs/ojmodule-element"],
  function (Bootstrap, ko, moduleUtils) {
    Bootstrap.whenDocumentReady().then(function () {
      function AppControllerViewModel() {
        const self = this;
        self.moduleConfig = ko.observable({ view: [], viewModel: null });
        moduleUtils
          .createConfig({
            name: "dashboard",
          })
          .then(function (config) {
            self.moduleConfig(config);
          });
      }

      ko.applyBindings(new AppControllerViewModel(), document.getElementById("app"));
    });
  }
);
