const load = async function load() {
    const count = await client.count();
    document.getElementById("totalItemsToSearch").innerHTML = "There are " + count['count'] + " items available to search."
    populateCountryDropdown();
    populateSavedSearches();
}

function populateCountryDropdown() {
    client.indices.getMapping({index: '*'}, function(error, response){
        var countries = [];
        for (var item in response) {
            for (var country in response[item]['mappings']) {
                if (countries.includes(country)) {
                    break;
                }
                else {
                    countries.push(country);
                }
            }
        }
        countryObj = {};
        for (var c in countries) {
            if (!countryObj.hasOwnProperty(countries[c])){
                countryObj[countries[c]] = [];
            }
        }
        for (var obj in response) {
            for (var key in countryObj) {
                if (response[obj]['mappings'].hasOwnProperty(key)) {
                    countryObj[key].push(obj.split("_").join(" "));
                }
                countryObj[key].sort();
            }
        }
        countryInnerHtml = "<option value=\"\" disabled selected hidden>Select Country</option><option value=\"\">None</option>";
        for (var country in countryObj) {
            countryInnerHtml += "<option>" + country + "</option>";
        }
        document.getElementById("countryDropdown").innerHTML = countryInnerHtml;
    });
}

function populateRegionDropdown() {
    var selectedCountry = $('#countryDropdown').val();
    var stateInnerHtml = "<option value=\"\" disabled selected hidden>Select Region</option><option value=\"\">None</option>";
    for (var region in countryObj[selectedCountry]) {
        stateInnerHtml += "<option class=\"stateListDropdown\">" + countryObj[selectedCountry][region] + "</option>";
    }
    document.getElementById("stateDropdown").innerHTML = stateInnerHtml;
}