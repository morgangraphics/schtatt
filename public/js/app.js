requirejs.config({
    paths: {
      app: "app",
      text: "lib/text",
      json: "lib/json",
      jquery: "lib/jquery-2.1.3.min",
      schtatt: "schtatt"
    }
});

// Load the main app module to start the app
requirejs(["app/main"]);