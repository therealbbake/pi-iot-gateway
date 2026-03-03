define([
  "knockout",
  "ojs/ojarraydataprovider",
  "ojs/ojchart",
  "ojs/ojtable",
  "ojs/ojformlayout",
  "ojs/ojinputtext",
  "ojs/ojinputnumber",
  "ojs/ojselectsingle",
  "ojs/ojbutton",
  "ojs/ojinputpassword",
  "text!js/views/dashboard.html",
], function (
  ko,
  ArrayDataProvider,
  _ojChart,
  _ojTable,
  _ojFormLayout,
  _ojInputText,
  _ojInputNumber,
  _ojSelectSingle,
  _ojButton,
  _ojInputPassword,
  view
) {
  function DashboardViewModel() {
    const self = this;

    self.view = view;
    self.protocolOptions = new ArrayDataProvider(
      [
        { value: "http", label: "HTTP" },
        { value: "mqtts", label: "MQTTS" },
      ],
      { keyAttributes: "value" }
    );

    self.formState = {
      protocol: ko.observable("http"),
      domain: ko.observable("example"),
      region: ko.observable("us-ashburn-1"),
      resource: ko.observable("sampletopic"),
      deviceId: ko.observable("pi-gateway-01"),
      samplingInterval: ko.observable(30),
      username: ko.observable("iot_client"),
      password: ko.observable(""),
    };

    self.actionMessage = ko.observable("");
    self.messageCss = ko.observable("");
    self.lastReadingText = ko.observable("No readings yet");
    self.lastStatusText = ko.observable("Unknown");
    self.lastStatusCss = ko.observable("");

    self.chartSeries = ko.observable(
      new ArrayDataProvider([], { keyAttributes: "name" })
    );
    self.tableDataProvider = ko.observable(
      new ArrayDataProvider([], { keyAttributes: "recorded_at" })
    );
    self.tableColumns = [
      { headerText: "Timestamp", field: "recorded_at" },
      { headerText: "Temp (°C)", field: "temperature_c" },
      { headerText: "Temp (°F)", field: "temperature_f" },
      { headerText: "Status", field: "transport_status" },
      { headerText: "Error", field: "transport_error" },
    ];

    self._sensorProvider = "mock";
    self._pollTimer = null;

    self.connected = function () {
      self._loadConfig();
      self._refreshData();
      self._pollTimer = window.setInterval(self._refreshData, 10000);
    };

    self.disconnected = function () {
      if (self._pollTimer) {
        window.clearInterval(self._pollTimer);
        self._pollTimer = null;
      }
    };

    self._setMessage = function (message, isError) {
      self.actionMessage(message);
      self.messageCss(isError ? "status-failure" : "status-success");
    };

    self._loadConfig = function () {
      fetch("/api/config")
        .then(self._checkResponse)
        .then(function (response) {
          const transport = response.transport;
          self.formState.protocol(transport.protocol);
          self.formState.domain(transport.domain);
          self.formState.region(transport.region);
          self.formState.resource(transport.resource);
          self.formState.deviceId(transport.device_id);
          self.formState.samplingInterval(transport.sampling_interval_sec);
          self._sensorProvider = transport.sensor_provider;
        })
        .catch(function (error) {
          self._setMessage("Failed to load configuration: " + error, true);
        });
    };

    self._refreshData = function () {
      fetch("/api/readings?limit=20")
        .then(self._checkResponse)
        .then(function (response) {
          const readings = response.readings || [];
          const chartData = [
            {
              name: "Temperature °C",
              items: readings
                .slice()
                .reverse()
                .map(function (item) {
                  return {
                    x: new Date(item.recorded_at).toLocaleTimeString(),
                    y: item.temperature_c,
                  };
                }),
            },
          ];
          self.chartSeries(
            new ArrayDataProvider(chartData, { keyAttributes: "name" })
          );
          self.tableDataProvider(
            new ArrayDataProvider(readings, { keyAttributes: "recorded_at" })
          );
          if (readings.length) {
            const latest = readings[0];
            self.lastReadingText(
              new Date(latest.recorded_at).toLocaleString() +
                " | " +
                latest.temperature_c.toFixed(2) +
                " °C"
            );
            self.lastStatusText(latest.transport_status);
            self.lastStatusCss(
              latest.transport_status === "success"
                ? "status-success"
                : "status-failure"
            );
          }
        })
        .catch(function (error) {
          self._setMessage("Failed to load readings: " + error, true);
        });
    };

    self._checkResponse = function (response) {
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      return response.json();
    };

    self.saveConfig = function () {
      const secretsPayload = {};
      if (self.formState.username()) {
        secretsPayload.username = self.formState.username();
      }
      if (self.formState.password()) {
        secretsPayload.password = self.formState.password();
      }

      const payload = {
        transport: {
          protocol: self.formState.protocol(),
          domain: self.formState.domain(),
          region: self.formState.region(),
          resource: self.formState.resource(),
          device_id: self.formState.deviceId(),
          sampling_interval_sec: self.formState.samplingInterval(),
          sensor_provider: self._sensorProvider,
        },
      };
      if (Object.keys(secretsPayload).length > 0) {
        payload.secrets = secretsPayload;
      }
      fetch("/api/config", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(self._checkResponse)
        .then(function () {
          self._setMessage("Configuration saved", false);
        })
        .catch(function (error) {
          self._setMessage("Save failed: " + error, true);
        });
    };

    self.testConnection = function () {
      fetch("/api/test-connection", { method: "POST" })
        .then(self._checkResponse)
        .then(function () {
          self._setMessage("Connection succeeded", false);
        })
        .catch(function (error) {
          self._setMessage("Connection failed: " + error, true);
        });
    };
  }

  return DashboardViewModel;
});
