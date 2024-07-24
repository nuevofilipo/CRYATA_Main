async function main(timeframe) {
    var currentPairAgainst = document.querySelector(".pairAgainst.active").value;
    const data = await getTableViewData("table" + timeframe, currentPairAgainst);
    var varvIndicator = [];
    var contextBands = [];
    var volatilityMean = [];

    // there is same data across timeframes for some indicators, so we have to fetch that
    if (timeframe !== "1d") {
      var DailyData = await getTableViewData("table1d", currentPairAgainst);
      varvIndicator = data.map((entry) => {
        const dailyEntry = DailyData.find((dailyEntry) => dailyEntry.coin === entry.coin);
        return dailyEntry ? dailyEntry.varvIndicator : "undefined";
      });
      contextBands = data.map((entry) => {
        const dailyEntry = DailyData.find((dailyEntry) => dailyEntry.coin === entry.coin);
        return dailyEntry ? dailyEntry.contextBands : "undefined";
      });
      volatilityMean = data.map((entry) => {
        const dailyEntry = DailyData.find((dailyEntry) => dailyEntry.coin === entry.coin);
        if (dailyEntry) {
          const key = `volatilityMean${timeframe}`;
          volatilityMean = dailyEntry[key];
          return volatilityMean;
        } else {
          return "undefined";
        }
      });
    } else {
      varvIndicator = data.map((entry) => entry.varvIndicator);
      contextBands = data.map((entry) => entry.contextBands);
      volatilityMean = data.map((entry) => entry.volatilityMean1d);
    }

    data.forEach(function (entry, index) {
      addRow(
        currentPairAgainst,
        entry.index,
        entry.coin,
        entry.price,
        entry.priceChange,
        contextBands[index],
        varvIndicator[index],
        entry.momentumIndicator,
        volatilityMean[index],
        entry.meanPerformance,
        entry.medianPerformance,
        entry.nearestZone
      );
    });
}


function addRow(currentPairAgainst, index, coin, price, priceChange, contextBands, varvIndicator, momentum, volatilityMean, meanPerformance, medianPerformance, nearestZone) {
  var table = document.getElementById("cryptoTable");
  var row = table.insertRow(-1); 
  row.setAttribute("data-coin", coin);

  // creating new cells
  var cell1 = row.insertCell(0);
  var cell2 = row.insertCell(1);
  var cell3 = row.insertCell(2);
  var cell3b = row.insertCell(3);
  var cell4 = row.insertCell(4);
  var cell5 = row.insertCell(5);
  var cell6 = row.insertCell(6);
  var cell7 = row.insertCell(7);
  var cell8 = row.insertCell(8);
  var cell9 = row.insertCell(9);
  var cell10 = row.insertCell(10);

  // setting values in cells
  cell1.innerHTML = index;
  cell2.innerHTML = coin;
  if (currentPairAgainst === "usd") {
    cell3.innerHTML = "$" + String(price);
  } else {
    cell3.innerHTML = String(price) + " BTC";
  }
  cell3b.innerHTML = String(priceChange) + " %";
  cell4.innerHTML = contextBands;
  if (varvIndicator === 0) {
    cell5.innerHTML = "below";
  } else if (varvIndicator === 11) {
    cell5.innerHTML = "above";
  } else {
    cell5.innerHTML = varvIndicator;
  }
  if (momentum === 1) {
    cell6.innerHTML = '<span style="font-size:30px; color: #26A69A;">&#8593;</span>'; // Upward arrow
  } else if (momentum === -1) {
    cell6.innerHTML = '<span style="font-size:30px; color: #EF5350;">&#8595;</span>'; // Downward arrow
  } else {
    cell6.innerHTML = '<span style="font-size:30px; color: #ffd073;">&#8594;</span>'; // No arrow if momentumIndicator is neither 1 nor -1
  }
  cell7.innerHTML = volatilityMean;
  cell8.innerHTML = meanPerformance;
  cell9.innerHTML = medianPerformance;
  cell10.innerHTML = nearestZone + " %";
  

  // aligning text
  cell2.style.textAlign = "left";
  cell3.style.textAlign = "right";
  cell3b.style.textAlign = "right";
  cell4.style.textAlign = "center";
  cell7.style.textAlign = "right";
  cell8.style.textAlign = "right";
  cell9.style.textAlign = "right";
  cell10.style.textAlign = "right";

  // styling the cells
  if (priceChange > 0) {
    cell3b.style.color = "#26A69A"; // green
  } else if (priceChange === 0) {
    cell3b.style.color = "#fffb85"; // yellow
  } else if (priceChange < 0) {
    cell3b.style.color = "#EF5350"; // red
  } else {
    cell3b.style.color = "white";
  }
  cell4.style.color = "white";
  if (contextBands === 2 || contextBands === 1) {
    cell4.style.color = "#EF5350";
    cell4.textContent = "short potential";
  } else if (contextBands === 0) {
    cell4.style.color = "#ffd073"; // orange
    cell4.textContent = "ranging";
  } else if (contextBands === -1 || contextBands === -2) {
    cell4.style.color = "#26A69A";
    cell4.textContent = "long potential";
  }
}

async function getTableViewData(tableName, currentPairAgainst) {
  if (currentPairAgainst === "usd") {
    currentPairAgainst = "";
  } else {
    currentPairAgainst = "_btc";
  }
  const response = await fetch(`https://table-view-api-production.up.railway.app/?name=${tableName}${currentPairAgainst}`);
  const data = await response.json();
  return data;
}

//! sorting functionality ------------------
var sortingState = {
  columnIndex: null,
  order: null,
};

function sortTable(columnIndex) {
  var table, rows, switching, i, x, y, shouldSwitch;

  addRemoveSortingIcon(columnIndex);

  table = document.getElementById("cryptoTable");
  switching = true;

  // Reset sorting state for other columns if a new column is clicked
  if (sortingState.columnIndex !== columnIndex) {
    sortingState.columnIndex = columnIndex;
    sortingState.order = "asc"; // Default to ascending order
  } else {
    // Toggle sorting order if the same column is clicked again
    sortingState.order = sortingState.order === "asc" ? "desc" : "asc";
  }

  while (switching) {
    switching = false;
    rows = table.rows;

    for (i = 1; i < rows.length - 1; i++) {
      shouldSwitch = false;
      x = rows[i].getElementsByTagName("td")[columnIndex];
      y = rows[i + 1].getElementsByTagName("td")[columnIndex];

      // Compare content based on sorting state for the column
      if (sortingState.order === "asc") {
        if (compareCells(x, y, sortingState.order) > 0) {
          shouldSwitch = true;
          break;
        }
      } else {
        if (compareCells(x, y, sortingState.order) < 0) {
          shouldSwitch = true;
          break;
        }
      }
    }

    if (shouldSwitch) {
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
    }
  }
}

// helper function for sortTable function
function compareCells(cellX, cellY, order) {
  var contentX = cellX.innerHTML.toLowerCase();
  var contentY = cellY.innerHTML.toLowerCase();
  var lastStrings = ["no data %", "not sufficient data", "nan %", "undefined"];

  const isLastString = (str) => lastStrings.includes(str);

  if (isLastString(contentX) && !isLastString(contentY)) {
    // contentX is in lastStrings, so it should come last
    return order === "asc" ? 1 : -1;
  } else if (!isLastString(contentX) && isLastString(contentY)) {
    // contentY is in lastStrings, so it should come last
    return order === "asc" ? -1 : 1;
  } else if (!isNaN(parseFloat(contentX)) && !isNaN(parseFloat(contentY))) {
    // If both contents are numeric, compare numerically
    return parseFloat(contentX) - parseFloat(contentY);
  } else {
    // Otherwise, compare as strings
    return contentX.localeCompare(contentY);
  }
}

//! update and change functions ------------------
// "change" functions that users can trigger
async function changeTimeFrame(event, timeframe) {
  // reset table
  updateTable(timeframe);
  console.log("Timeframe changed to: " + timeframe);
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  event.currentTarget.className += " active";
}

function changePairAgainst(event, pairAgainst) {
  var options = document.querySelectorAll(".pairAgainst");
  for (var i = 0; i < options.length; i++) {
    options[i].classList.remove("active");
  }
  event.currentTarget.classList.add("active");
  var currTimeframe = document.querySelector(".tablinks.active").getAttribute("data-timeframe");
  updateTable(currTimeframe);
}


async function updateTable(timeframe) {
  var table = document.getElementById("cryptoTable");
  table.innerHTML =
    "<tr class='headerTr'><th class='center-th' onclick='sortTable(0)'>#</th><th class='left-th' onclick='sortTable(1)'>Coin</th><th class='right-th' onclick='sortTable(2)'>Price</th><th class='right-th' onclick='sortTable(3)'>Change</th><th class='center-th' onclick='sortTable(4)'>Context Bands</th><th class='center-th' onclick='sortTable(5)'>VARV</th><th class='center-th' onclick='sortTable(6)'>Momentum</th><th class='right-th' onclick='sortTable(7)'>Volatility</th><th class='right-th' onclick='sortTable(8)'>Mean Performance</th><th class='right-th' onclick='sortTable(9)'>Median Performance</th><th class='right-th' onclick='sortTable(10)'>nearest zone</th></tr>";
  main(timeframe);
}



//! html functionality ------------------
function addRemoveSortingIcon(columnIndex) {
  var headers = document.getElementsByTagName("th");

  for (var i = 0; i < headers.length; i++) {
    if (i == columnIndex) continue;
    headers[i].classList.remove("asc", "desc");
    headers[i].innerHTML = headers[i].innerText; // Remove the sorting arrows
  }
  var th = headers[columnIndex];
  // toggle between ascending and descending
  if (th.classList.contains("asc")) {
    th.classList.remove("asc");
    th.classList.add("desc");
    if (th.classList.contains("right-th")) {
      th.innerHTML = '<i class="fa fa-caret-down"></i> ' + th.innerText;
    } else {
      th.innerHTML = th.innerText + ' <i class="fa fa-caret-down"></i>';
    }
  } else {
    th.classList.remove("desc");
    th.classList.add("asc");
    if (th.classList.contains("right-th")) {
      th.innerHTML = '<i class="fa fa-caret-up"></i> ' + th.innerText;
    } else {
      th.innerHTML = th.innerText + ' <i class="fa fa-caret-up"></i>';
    }
  }
}

function goToChartViewPage(coin) {
  var timeframe = document.querySelector(".tablinks.active").getAttribute("data-timeframe");
  // change when not in local
  window.location.href = `http://127.0.0.1:5501/frontend/html-files/chartViewPage.html?coin=${coin}&timeframe=${timeframe}`;
}

function scrollFunction() {
  if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    mybutton.style.display = "block";
  } else {
    mybutton.style.display = "none";
  }
}

//! event listeners ------------------
// for going to the chartviewpage upon click on some coins row
document.getElementById("cryptoTable").addEventListener("click", function (event) {
  const tr = event.target.closest("tr");
  if (tr != null && !tr.classList.contains("headerTr")) {
    const coin = tr.getAttribute("data-coin");
    const timeframe = document.querySelector(".active").getAttribute("data-timeframe");
    var pairAgainst = document.querySelector(".pairAgainst.active").value;
    var coinPair = coin + "/USD";
    if (pairAgainst === "btc") {
      coinPair = coin + "/BTC";
    }
    if (coin !== null) {
      goToChartViewPage(coinPair);
    }
  }
});

// for scrolling to top on button click
let mybutton = document.getElementById("backToTopBtn");
mybutton.onclick = function () {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
};

window.onscroll = function () {
  scrollFunction();
};


//! initial call ------------------
async function init() {
  await main("1d");
}

document.addEventListener("DOMContentLoaded", init);
