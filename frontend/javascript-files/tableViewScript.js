// Function to add a new row to the table
function addRow(
  index,
  coin,
  price,
  priceChange,
  contextBands,
  varvIndicator,
  momentum,
  volatilityMean,
  meanPerformance,
  medianPerformance
) {
  var table = document.getElementById("cryptoTable");
  var row = table.insertRow(-1); // Insert row at the end of the table
  row.setAttribute("data-coin", coin);

  var cell1 = row.insertCell(0);
  var cell2 = row.insertCell(1);
  cell2.style.textAlign = "left";

  var cell3 = row.insertCell(2);
  var cell3b = row.insertCell(3);
  if (priceChange > 0) {
    cell3b.style.color = "#26A69A"; // green
  } else if (priceChange === 0) {
    cell3b.style.color = "#fffb85"; // yellow
  } else if (priceChange < 0) {
    cell3b.style.color = "#EF5350"; // red
  } else {
    cell3b.style.color = "white";
  }

  var cell4 = row.insertCell(4);
  cell4.style.textAlign = "right";
  var cell5 = row.insertCell(5);
  var cell6 = row.insertCell(6);
  var cell7 = row.insertCell(7);
  var cell8 = row.insertCell(8);
  var cell9 = row.insertCell(9);

  cell1.innerHTML = index;
  cell2.innerHTML = coin;
  cell3.innerHTML = price;
  cell3.style.textAlign = "right";
  cell3b.innerHTML = String(priceChange) + " %";
  cell3b.style.textAlign = "right";
  // cell3b.innerHTML = priceChange;
  cell4.innerHTML = contextBands;
  cell4.style.color = "black";
  cell4.style.textAlign = "center";

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

  if (varvIndicator === 0) {
    cell5.innerHTML = "below";
  } else if (varvIndicator === 11) {
    cell5.innerHTML = "above";
  } else {
    cell5.innerHTML = varvIndicator;
  }

  // adding arrows for momentum
  if (momentum === 1) {
    cell6.innerHTML =
      '<span style="font-size:30px; color: #26A69A;">&#8593;</span>'; // Upward arrow
  } else if (momentum === -1) {
    cell6.innerHTML =
      '<span style="font-size:30px; color: #EF5350;">&#8595;</span>'; // Downward arrow
  } else {
    cell6.innerHTML =
      '<span style="font-size:30px; color: #ffd073;">&#8594;</span>'; // No arrow if momentumIndicator is neither 1 nor -1
  }

  cell7.innerHTML = volatilityMean;
  cell8.innerHTML = meanPerformance;
  cell9.innerHTML = medianPerformance;

  cell7.style.textAlign = "right";
  cell8.style.textAlign = "right";
  cell9.style.textAlign = "right";
}

// Object to keep track of sorting state for the current column
var sortingState = {
  columnIndex: null,
  order: null,
};

function addRemoveSortingIcon(columnIndex) {
  // Get all table headers
  var headers = document.getElementsByTagName("th");

  // Remove existing sort classes and icons from all headers
  for (var i = 0; i < headers.length; i++) {
    if (i == columnIndex) continue;

    headers[i].classList.remove("asc", "desc");
    headers[i].innerHTML = headers[i].innerText; // Remove any icons
  }

  // Get the header for the specified column
  var th = headers[columnIndex];

  // Toggle between ascending and descending states
  if (th.classList.contains("asc")) {
    // If currently ascending, switch to descending
    th.classList.remove("asc");
    th.classList.add("desc");
    if (th.classList.contains("right-th")) {
      th.innerHTML = '<i class="fa fa-caret-down"></i> ' + th.innerText;
    } else {
      th.innerHTML = th.innerText + ' <i class="fa fa-caret-down"></i>';
    }
  } else {
    // If not currently ascending, switch to ascending
    th.classList.remove("desc");
    th.classList.add("asc");
    if (th.classList.contains("right-th")) {
      th.innerHTML = '<i class="fa fa-caret-up"></i> ' + th.innerText;
    } else {
      th.innerHTML = th.innerText + ' <i class="fa fa-caret-up"></i>';
    }
  }
}

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

// Function to compare cell content
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

// Function to fetch data from the API
async function getTableViewData(tableName) {
  const response = await fetch(
    `https://table-view-api-production.up.railway.app/?name=${tableName}`
  );
  const data = await response.json();
  return data;
}

// Loop through API response and add rows to the table
async function main(timeframe) {
  const data = await getTableViewData("table" + timeframe);
  var DailyData = null;
  var varvIndicator = [];
  var contextBands = [];
  var volatilityMean = [];
  if (timeframe !== "1d") {
    DailyData = await getTableViewData("table1d");
    varvIndicator = data.map((entry) => {
      const dailyEntry = DailyData.find(
        (dailyEntry) => dailyEntry.coin === entry.coin
      );
      return dailyEntry ? dailyEntry.varvIndicator : "undefined";
    });
    contextBands = data.map((entry) => {
      const dailyEntry = DailyData.find(
        (dailyEntry) => dailyEntry.coin === entry.coin
      );
      return dailyEntry ? dailyEntry.contextBands : "undefined";
    });
    volatilityMean = data.map((entry) => {
      const dailyEntry = DailyData.find(
        (dailyEntry) => dailyEntry.coin === entry.coin
      );
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
      entry.index,
      entry.coin,
      entry.price,
      entry.priceChange,
      contextBands[index],
      varvIndicator[index],
      entry.momentumIndicator,
      volatilityMean[index],
      entry.meanPerformance,
      entry.medianPerformance
    );
  });

  headerTr = document.getElementsByClassName("headerTr");
}

async function changeTimeFrame(event, timeframe) {
  // reset table
  var table = document.getElementById("cryptoTable");
  table.innerHTML =
    "<tr class='headerTr'><th onclick='sortTable(0)'>#</th><th onclick='sortTable(1)'>Coin</th><th onclick='sortTable(2)'>Price (USD)</th><th onclick='sortTable(3)'>Change %</th><th onclick='sortTable(4)'>Context Bands</th><th onclick='sortTable(5)'>Varv</th><th onclick='sortTable(6)'>Momentum</th><th onclick='sortTable(7)'>VolatilityMean</th><th onclick='sortTable(8)'>Mean Performance</th><th onclick='sortTable(9)'>median Performance</th></tr>";
  main(timeframe);
  console.log("Timeframe changed to: " + timeframe);
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  event.currentTarget.className += " active";
}

// Event delegation to handle clicks on dynamically added rows
document
  .getElementById("cryptoTable")
  .addEventListener("click", function (event) {
    // Find the closest tr element to the clicked target
    const tr = event.target.closest("tr");
    // Check if the tr element exists and does not have the headerTr class
    if (tr != null && !tr.classList.contains("headerTr")) {
      const coin = tr.getAttribute("data-coin");
      const timeframe = document
        .querySelector(".active")
        .getAttribute("data-timeframe");
      const coinPair = coin + "/USD";
      if (coin !== null) {
        goToChartViewPage(coinPair);
      }
    }
  });



//! html functionality
function goToChartViewPage(coin) {
    // for this to work, the local host of the chart view page has to be open
    var timeframe = document.querySelector(".tablinks.active").getAttribute("data-timeframe");
   window.location.href = `http://127.0.0.1:5500/frontend/html-files/chartViewPage.html?coin=${coin}&timeframe=${timeframe}`;
}

let mybutton = document.getElementById("backToTopBtn");
window.onscroll = function () {
  scrollFunction();
};
function scrollFunction() {
  if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    mybutton.style.display = "block";
  } else {
    mybutton.style.display = "none";
  }
}
mybutton.onclick = function () {
  window.scrollTo({
    top: 0,
    behavior: "smooth",
  });
};

//! Initial call to populate table with data
main("1d");
