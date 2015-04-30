define(["jquery"], function($){

    var obs = (function(){
      var map;
      var config = {}
      var mapOptions = {
        center: new google.maps.LatLng(41.850033,-87.6500523),
        zoom: 13
      };

      var response = '';
      var map = ''
      var trips = []
      var details = []
      var heat = []
      var heatmap = ''

      function clearMap(){
        
        while(trips[0]){
          trips.pop().setMap(null)
        }
        trips.length = 0
        if(heatmap != ''){ heatmap.setMap(null); }
      }
      function displayCluster(){
        var cnt = 0;
        for(var i = 0, lenD = response.length; i < lenD; i++){
            day = response[i]
            $.each(day, function(key, value){
              for(var j = 0, lenT = value.length; j < lenT; j++){

                startObj = (value[j].startCoords.length > 0)? JSON.parse(value[j].startCoords[0].replace(/'/g, '"')) : false
                endObj = (value[j].endCoords.length > 0)? JSON.parse(value[j].endCoords[0].replace(/'/g, '"')) : false

                var populationOptions = {
                  strokeColor: '#000',
                  strokeOpacity: 1,
                  strokeWeight: 1,
                  fillOpacity: 0.35,
                  map: map,
                  radius: 100
                };

                if (startObj){
                  populationOptions.fillColor = '#ff0000',
                  populationOptions.center = startObj
                  trips.push(new google.maps.Circle(populationOptions));
                }

                if (endObj){
                  populationOptions.fillColor = '#0000ff',
                  populationOptions.center = endObj
                  trips.push(new google.maps.Circle(populationOptions));
                }

               
                  
                  // Add the circle for this city to the map.
                  cnt++
          
              }
            })
        }
      }
      
      function displayHeat(){
        map.setMapTypeId(google.maps.MapTypeId.SATELLITE)

        for(var i = 0, lenD = response.length; i < lenD; i++){
            day = response[i]

            $.each(day, function(key, value){
              for(var j = 0, lenT = value.length; j < lenT; j++){
                //Object comes in as a string. We change out the quotes and parse the JSON object to get it working. 
                //Eliminates the need to use unvetted eval() to convert the string to an array of objects
                coordsObj = JSON.parse(value[j].tripMapCoords.replace(/'/g, '"'))

                for(var k = 0, lenC = coordsObj.length; k < lenC; k++){
                  heat.push(new google.maps.LatLng(coordsObj[k].lat, coordsObj[k].lng))
                }
                //heat.push(coordsObj)

              }
            })
        }

       

        var pointArray = new google.maps.MVCArray(heat);

        //console.log(heat)
        //console.log(pointArray)

        heatmap = new google.maps.visualization.HeatmapLayer({
          data: pointArray
        });

        //console.log(heatmap)

        heatmap.setMap(map);
      }
      function displayLine(){
        var cnt = 0;
        for(var i = 0, lenD = response.length; i < lenD; i++){
            day = response[i]

            $.each(day, function(key, value){
              for(var j = 0, lenT = value.length; j < lenT; j++){

                //Object comes in as a string. We change out the quotes and parse the JSON object to get it working. 
                //Eliminates the need to use unvetted eval() to convert the string to an array of objects
                coordsObj = JSON.parse(value[j].tripMapCoords.replace(/'/g, '"'))

                trips[cnt] = new google.maps.Polyline({
                  path: coordsObj,
                  geodesic: true,
                  strokeColor: '#FF0000',
                  strokeOpacity: 1.0,
                  strokeWeight: 2,
                  polyLineID: cnt,
                  zIndex: cnt
                });

                details[cnt] = {
                  day: key,
                  earnings: value[j].earnings,
                  milage: value[j].milage
                }

                trips[cnt].setMap(map);

                google.maps.event.addListener(trips[cnt], 'mouseover', function(a) {
                  //console.log(this, a)
                  this.setMap(null);
                  this.strokeColor = "#00f"
                  this.zIndex = trips.length+1
                  this.setMap(map);

                  document.getElementById("tripDetail").style.top = a.gb.clientY - 80 + "px";
                  document.getElementById("tripDetail").style.left = a.gb.clientX + "px";
                  document.getElementById("tripDetail").innerHTML = details[this.polyLineID].day + '</br>' + details[this.polyLineID].earnings
                  document.getElementById("tripDetail").style.display = "block"
                })
                google.maps.event.addListener(trips[cnt], 'mouseout', function(a) {
                  //console.log(this, a)
                  this.setMap(null);
                  this.strokeColor = "#f00"
                  this.zIndex = this.polyLineID
                  this.setMap(map);
                  document.getElementById("tripDetail").style.display = "none"
                })

                cnt++;
              }
            })
        }
      }
      function events(){
        
        jQuery('#map-type').on('change', function(e){
          var val = e.target.value
          clearMap();
          map.setMapTypeId(google.maps.MapTypeId.ROADMAP)
          switch (val){
            case "line":
              displayLine();
            break;
            case "cluster":
              displayCluster();
            break;
            case "heat":
              displayHeat();
            break;

          }
        });
      }
      function init() {
            //Load some configuration options
            $.ajax({
              url: 'config.json',
              complete: function(data){
                response = data.responseJSON;
          
                mapOptions.center = new google.maps.LatLng(response.home.latitude, response.home.longitude)

                map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);

                google.maps.event.addDomListener(window, 'load', init);
              }
            });

            $.ajax({
              url: 'data.json',
              complete: function(data){
                response = data.responseJSON;
                displayLine();
                //displayCluster();
                //displayHeat();
              }
            });

            events();
            

      }
      return {
        init: init()
      }
    }())




})









