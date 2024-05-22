// defining the chart and other chart elements ----------------------------------------------
const mainSection = document.getElementById("tvchart");


function getMainHeight() {
  return mainSection.clientHeight;
}
function getMainWidth() {
  return mainSection.clientWidth;
}

const chartProperties = {
  height: getMainHeight() ,
  width: getMainWidth(),
  layout: {
    background: { color: "#000" },
    textColor: "#C3BCDB",
  },
  grid: {
    vertLines: { color: "#444", visible:false },
    horzLines: { color: "#444", visible: false },
  },
};

const domElement = document.getElementById("tvchart");
const chart = LightweightCharts.createChart(domElement, chartProperties);
const candleSeries = chart.addCandlestickSeries();

window.addEventListener("resize", () => {
  chart.resize(getMainWidth(), getMainHeight());
  console.log("resized");
});


// creating lines for the 4 line indicator
const maLine1 = chart.addLineSeries({ color: "#2196F3", lineWidth: 2, priceLineVisible: false });
const maLine2 = chart.addLineSeries({ color: "#2196F3", lineWidth: 2 , priceLineVisible: false});
const emaLine1 = chart.addLineSeries({ color: "violet", lineWidth: 1, priceLineVisible: false });
const emaLine2 = chart.addLineSeries({ color: "violet", lineWidth: 1, priceLineVisible: false });


// creating lines for the varv indicator
const band1 = chart.addLineSeries({ color: "#f73434", lineWidth: 1, priceLineVisible: false });
const band2 = chart.addLineSeries({ color: "#f74434", lineWidth: 1, priceLineVisible: false });
const band3 = chart.addLineSeries({ color: "#f7dd34", lineWidth: 1, priceLineVisible: false });
const band4 = chart.addLineSeries({ color: "#34f741", lineWidth: 1, priceLineVisible: false });
const band5 = chart.addLineSeries({ color: "#34f7d7", lineWidth: 1, priceLineVisible: false });
const band6 = chart.addLineSeries({ color: "#34b3f7", lineWidth: 1, priceLineVisible: false });
const band7 = chart.addLineSeries({ color: "#2196F3", lineWidth: 1, priceLineVisible: false });
const band8 = chart.addLineSeries({ color: "#5b34f7", lineWidth: 1, priceLineVisible: false });
const band9 = chart.addLineSeries({ color: "#dd34f7", lineWidth: 1, priceLineVisible: false });
const band10 = chart.addLineSeries({ color: "#e434f7", lineWidth: 1, priceLineVisible: false });
const band11 = chart.addLineSeries({ color: "#f73472", lineWidth: 1, priceLineVisible: false });

var addedBoxes = [];
let addedSupplyZones = new Map();
var addedBoxes2 = [];
var addedBoxes3 = [];
var addedRanges = [];
var addedRanges3m = [];
var addedRanges1m = [];
var addedRanges1w = [];
var addedRanges1d = [];

// functions for fetchng data asyncronously ----------------------------------------------


// for use with local data
async function getData(route){
  
  const selectedBtn = document.querySelector(".active");
  const response = await fetch(
    `http://127.0.0.1:5000/api/${route}/?coin=${updateCoin()}&timeframe=${selectedBtn.value}` 
  )
  
  const data = await response.json();
  return data;
}

async function getRangesData(range_value){
  const selectedBtn = document.querySelector(".active");
  const response = await fetch(
    `http://127.0.0.1:5000/api/ranges/?coin=${updateCoin()}&timeframe=${selectedBtn.value}&ranges=${range_value}` 
  )
  
  const data = await response.json();
  return data;

}

async function getDataIndividualTimeframe(endpoint, additionalParameter,  indicatorTimeframe){
  const chartTimeframe = document.querySelector('.tablinks.active').getAttribute('data-timeframe');
  const response = await fetch(
    `http://127.0.0.1:5000/api/${endpoint}/?coin=${updateCoin()}&timeframe=${chartTimeframe}&${additionalParameter}=${indicatorTimeframe}` 
  )

  const data = await response.json();
  return data;
    
}


// for use with external hosted data
// async function getData(route){
  
//   const selectedBtn = document.querySelector(".active");
//   const response = await fetch(
//     `https://cryatabackendv2-production.up.railway.app/api/${route}/?coin=${updateCoin()}&timeframe=${selectedBtn.value}` 
//   )
  
//   const data = await response.json();
//   return data;
// }

// async function getRangesData(range_value){
//   const selectedBtn = document.querySelector(".active");
//   const response = await fetch(
//     `https://cryatabackendv2-production.up.railway.app/api/ranges/?coin=${updateCoin()}&timeframe=${selectedBtn.value}&ranges=${range_value}` 
//   )
  
//   const data = await response.json();
//   return data;

// }



async function createBoxesData(mapping, functionToApply, color, key){
  list = [];
  const data = await functionToApply;
  data.forEach(element => {
    const i = candleSeries.createBox({
        lowPrice: element["y0"],
        highPrice: element["y1"],
        earlyTime: element["x0"] / 1000,
        lateTime: element["x1"] / 1000,
        borderColor: '#00008B',
        borderWidth: 2,
        borderStyle: LightweightCharts.LineStyle.Solid,
        fillColor: color,
        fillOpacity: 0.5,
        borderVisible: false,
        axisLabelVisible: false,
        title: 'My box',
      })
      list.push(i);
    });
  mapping.set(key, list);
}

async function createBoxesData2(list, functionToApply){ // this is for momentum
  const data = await functionToApply;
  console.log(data);

  data.forEach(element => {
    const i = candleSeries.createBox({
        lowPrice: element["y0"],
        highPrice: element["y1"],
        earlyTime: element["x0"] / 1000,
        lateTime: element["x1"] / 1000,
        borderColor: '#00008B',
        borderWidth: 2,
        borderStyle: LightweightCharts.LineStyle.Solid,
        fillColor: element["color"],
        fillOpacity: 0.4,
        borderVisible: false,
        axisLabelVisible: false,
        title: 'My box',
      })
      list.push(i);
    });
  }
async function createRangesData(list, functionToApply, color){
  const data = await functionToApply;
  console.log(data);

  data.forEach(element => {
    const i = candleSeries.createBox({
        corners: [{ time: element["x0"] / 1000, price: element["y0"] }, { time: element["x1"] / 1000, price: element["y1"] }],
        borderColor: color,
        borderWidth: 2,
        borderStyle: LightweightCharts.LineStyle.Solid,
        fillColor: color,
        fillOpacity: 0.4,
        borderVisible: true,
        axisLabelVisible: false,
        title: 'My box',
      })
      list.push(i);
    });
  }



function removeBoxes(list){
  list.forEach(element => {
    candleSeries.removeBox(element);
  });
  list = [];
}

function removeBoxesMap(mapping, key){
  boxes = mapping.get(key);
  boxes.forEach(element => {
    candleSeries.removeBox(element);
  });
  mapping.delete(key);
}




// functions for setting data----------------------------------------------

async function setData(){
  const data = await getData("query"); 
  const cdata = data.map((d) => {
    try {
      returnState = {
        time: d.time / 1000, 
        open: parseFloat(d.Open),
        high: parseFloat(d.High),
        low: parseFloat(d.Low),
        close: parseFloat(d.Close),
        movingAverage: parseFloat(d.MA),
        ema: parseFloat(d.EMA),
      };
    } catch {
      returnState = {
        time: d.time / 1000, 
        open: parseFloat(d.Open),
        high: parseFloat(d.High),
        low: parseFloat(d.Low),
        close: parseFloat(d.Close),
      };
    }
    return returnState;
    
  });
  candleSeries.setData(cdata);
  chart.priceScale("right").applyOptions({
    autoScale: true,
    mode: 1,
  });
  chart.timeScale().applyOptions({
    timeVisible: true,
  })
}


async function setLineData(){
  data = await getData("4lines");
  const maDownShift = data.map((d) => {
    return { value: parseFloat(d.MA)*0.62, time: d.time / 1000 };
  });
  const maUpShift = data.map((d) => {
    return { value: parseFloat(d.MA)*1.62, time: d.time / 1000 };
  });
  const emaDownShift = data.map((d) => {
    return { value: parseFloat(d.EMA)*0.79, time: d.time / 1000 };
  });
  const emaUpShift = data.map((d) => {
    return { value: parseFloat(d.EMA)*1.21, time: d.time / 1000 };
  });

  if (indicatorState() == true){
  maLine1.setData(maDownShift);
  maLine2.setData(maUpShift);
  emaLine1.setData(emaDownShift);
  emaLine2.setData(emaUpShift);
  } else if (indicatorState() == false){
    maLine1.setData([]);
    maLine2.setData([]);
    emaLine1.setData([]);
    emaLine2.setData([]);
  }
}

async function setVarvData(){
  data = await getData("varv");
  const band1Data = data.map((d) => {
    return { value: parseFloat(d.out1), time: d.time / 1000 };
  });
  const band2Data = data.map((d) => {
    return { value: parseFloat(d.out2), time: d.time / 1000 };
  });
  const band3Data = data.map((d) => {
    return { value: parseFloat(d.out3), time: d.time / 1000 };
  });
  const band4Data = data.map((d) => {
    return { value: parseFloat(d.out4), time: d.time / 1000 };
  });
  const band5Data = data.map((d) => {
    return { value: parseFloat(d.out5), time: d.time / 1000 };
  });
  const band6Data = data.map((d) => {
    return { value: parseFloat(d.out6), time: d.time / 1000 };
  });
  const band7Data = data.map((d) => {
    return { value: parseFloat(d.out7), time: d.time / 1000 };
  });
  const band8Data = data.map((d) => {
    return { value: parseFloat(d.out8), time: d.time / 1000 };
  });
  const band9Data = data.map((d) => {
    return { value: parseFloat(d.out9), time: d.time / 1000 };
  });
  const band10Data = data.map((d) => {
    return { value: parseFloat(d.out10), time: d.time / 1000 };
  });
  const band11Data = data.map((d) => {
    return { value: parseFloat(d.out11), time: d.time / 1000 };
  });


  

  if (varvIndicatorState() == true){
  band1.setData(band1Data);
  band2.setData(band2Data);
  band3.setData(band3Data);
  band4.setData(band4Data);
  band5.setData(band5Data);
  band6.setData(band6Data);
  band7.setData(band7Data);
  band8.setData(band8Data);
  band9.setData(band9Data);
  band10.setData(band10Data);
  band11.setData(band11Data);
  } else if (varvIndicatorState() == false){
    band1.setData([]);
    band2.setData([]);
    band3.setData([]);
    band4.setData([]);
    band5.setData([]);
    band6.setData([]);
    band7.setData([]);
    band8.setData([]);
    band9.setData([]);
    band10.setData([]);
    band11.setData([]);
  }
}






function setBoxes(){
  removeBoxes(addedBoxes);
  if (zonesIndicatorState() == true){
    createBoxesData(addedBoxes, getData("zones"), '#e82ec0');
  } else if (zonesIndicatorState() == false){
    removeBoxes(addedBoxes);
  }
}

function setBoxes2(){
  removeBoxes(addedBoxes2);
  if (zones2IndicatorState() == true){
    createBoxesData(addedBoxes2, getData("zones2"), '#a7b4c9');
  } else if (zones2IndicatorState() == false){
    removeBoxes(addedBoxes2);
  }
}

function setMomentum(){
  removeBoxes(addedBoxes3);
  if (momentumIndicatorState() == true){
    createBoxesData2(addedBoxes3, getData("momentum"));
  } else if (momentumIndicatorState() == false){
    removeBoxes(addedBoxes3);
  }
}

function setRanges(range_value, list, color){
  removeBoxes(list);
  if (rangeIndicatorState(range_value) == true){
    createRangesData(list, getRangesData(range_value), color);
  } else if (rangeIndicatorState(range_value) == false){
    removeBoxes(list);
  }
}


function setAll(){
  setData();
  setLineData();
  setVarvData();
  // setBoxes();
  // setBoxes2();
  setMomentum();
  setRanges("1y", addedRanges, '#e02bd4');
  setRanges("3m", addedRanges3m, '#ffdd00');
  setRanges("1m", addedRanges1m, '#03c4ff');
  setRanges("1week", addedRanges1w, '#ff03a3');
  setRanges("1day", addedRanges1d, '#03ff81');
  updateIndividualIndicatorsTimeframe();
}




setData(); // changed this because otherwise api calls get wasted, each time
updateIndividualIndicatorsTimeframe();




// updating queries (coin and timeframe) ----------------------------------------------

function updateTimeframe(event, timeframe) {
  var i, tablinks;

  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  event.currentTarget.className += " active";
  setAll();
  
}


function updateIndividualIndicatorsTimeframe(){
  const individualTimeframeButtons = document.querySelectorAll('.timeframe-btn');
  const timeframeRanks = {
    '1h': 1,
    '4h': 2,
    '1day': 3,
    '1week': 4
  };
  const selectedTimeframe = document.querySelector('.tablinks.active').getAttribute('data-timeframe');
  console.log(selectedTimeframe);
  const selectedRank = timeframeRanks[selectedTimeframe];

  individualTimeframeButtons.forEach(button => {
    const buttonTimeframe = button.getAttribute('data-timeframe');
    const buttonRank = timeframeRanks[buttonTimeframe];
    const indicatorType = button.getAttribute('data-indicator');

    if (buttonRank < selectedRank) {
      button.disabled = true;
      button.classList.add('disabled');
      if (button.classList.contains('active')) {
        button.classList.remove('active');
        removeBoxesMap(addedSupplyZones, indicatorType + buttonTimeframe);
      }
    } else {
      button.disabled = false;
      button.classList.remove('disabled');
    }
  });

}

function updateCoin(){
  const selectedCoin = document.getElementById("coin-selector").value;
  return selectedCoin;
}




// element listeners ----------------------------------------------


const switchElement = document.getElementById("indicator-switch");
switchElement.addEventListener("change", function(){
  setLineData();
})


// const zonesSwitchElement = document.getElementById("zones-indicator-switch");
// zonesSwitchElement.addEventListener("change", function(){
//   setBoxes();
// });

// const zonesSwitchElement2 = document.getElementById("zones2-indicator-switch");
// zonesSwitchElement2.addEventListener("change", function(){
//   setBoxes2();
//   console.log("switched")
// });

const momentumSwitchElement = document.getElementById("momentum-indicator-switch");
momentumSwitchElement.addEventListener("change", function(){
  setMomentum();
  console.log("switched")
});

const varvSwitchElement = document.getElementById("varv-indicator-switch");
varvSwitchElement.addEventListener("change", function(){
  setVarvData();
  console.log("switched")
});

const rangeSwitchElement = document.getElementById("1y");
rangeSwitchElement.addEventListener("change", function(){
  setRanges("1y", addedRanges, '#e02bd4');
  console.log("switched")
});

const switchElement3m = document.getElementById("3m");
switchElement3m.addEventListener("change", function(){
  setRanges("3m", addedRanges3m, '#ffdd00');
  console.log("switched")
});

const switchElement1m = document.getElementById("1m");
switchElement1m.addEventListener("change", function(){
  setRanges("1m", addedRanges1m, '#03c4ff');
  console.log("switched")
});

const switchElement1w = document.getElementById("1week");
switchElement1w.addEventListener("change", function(){
  setRanges("1week", addedRanges1w, '#ff03a3');
  console.log("switched")
});

const switchElement1d = document.getElementById("1day");
switchElement1d.addEventListener("change", function(){
  setRanges("1day", addedRanges1d, '#03ff81');
  console.log("switched")
});

// small individual timeframe buttons
const Buttons = document.querySelectorAll('.timeframe-btn');
Buttons.forEach(button => {
    button.addEventListener('click', function() {
        this.classList.toggle('active');
        const indTime = button.getAttribute('data-timeframe');
        const indicatorType = button.getAttribute('data-indicator');
        const color = button.getAttribute('data-color');
        if (button.classList.contains('active')) {
          createBoxesData(addedSupplyZones, getDataIndividualTimeframe( indicatorType, "indicatorTimeframe",  indTime), color, indicatorType + indTime );
        } else {
          // Optionally handle the case when the button is not active
          removeBoxesMap(addedSupplyZones, indicatorType + indTime);
        }
        console.log("clicked");
    });
});


// state functions ----------------------------------------------

function indicatorState(){
  const indicatorSwitch = document.getElementById("indicator-switch");
  if (indicatorSwitch.checked){
    return true;
  }
  else if (indicatorSwitch.checked == false){
    return false;
  }
}

function zonesIndicatorState(){
  const zonesSwitch = document.getElementById("zones-indicator-switch");
  if (zonesSwitch.checked){
    return true;
  }
  else if (zonesSwitch.checked == false){
    return false;
  }
}

function zones2IndicatorState(){
  const zonesSwitch2 = document.getElementById("zones2-indicator-switch");
  if (zonesSwitch2.checked){
    return true;
  }
  else if (zonesSwitch2.checked == false){
    return false;
  }
}


function momentumIndicatorState(){
  const momentumSwitch = document.getElementById("momentum-indicator-switch");
  if (momentumSwitch.checked){
    return true;
  }
  else if (momentumSwitch.checked == false){
    return false;
  }
}

function varvIndicatorState(){
  const varvSwitch = document.getElementById("varv-indicator-switch");
  if (varvSwitch.checked){
    return true;
  }
  else if (varvSwitch.checked == false){
    return false;
  }
}

function rangeIndicatorState(range_indicator_id){
  const rangeSwitch = document.getElementById(range_indicator_id);
  if (rangeSwitch.checked){
    return true;
  }
  else if (rangeSwitch.checked == false){
    return false;
  }
}



// const horizontalBox = { 
//   corners: [{ time: 1687708800, price: 24000 }, { time: 1693526400, price: 22000 }],
//   borderColor: '#ededed',
//   borderWidth: 2,
//   borderStyle: LightweightCharts.LineStyle.Solid,
//   fillColor: '#e82ec0',
//   fillOpacity: 0.4,
//   borderVisible: true,
//   axisLabelVisible: false,
//   title: 'My box',
// };


