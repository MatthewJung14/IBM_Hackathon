//florida_map.js
const map = L.map('map').setView([27.9944024, -81.7602544], 7); // Centered on Florida

// Map tile layer
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

const redIcon = new L.Icon({
    iconUrl: '../../static/assets/img/location_11970459.png',
    iconSize: [30, 33],
    iconAnchor: [15, 30]
});

// Fetch data from the API
fetch('http://localhost:5000/api/data-lists')
    .then(response => response.json())
    .then(data => {
        const donationList = data.donated_items;
        const neededList = data.wanted_items;
        const connectList = data.item_links;

        const locationsInstance = new Locations(donationList, neededList, connectList);
        const donationLocations = locationsInstance.getDonationLocations();
        const neededLocations = locationsInstance.getNeededLocations();
        const connectedLocations = locationsInstance.getConnectionLocations();

        // Define custom colors for the icons
        const neededColour = '#E3242B';  // Red for needed locations
        const donationColour = '#1E90FF'; // Blue for donation locations
        const connectionColor = '#800080'; // Purple for connected locations

        // Create icon styles for each type
        const createIcon = (color) => {
            return L.divIcon({
                className: "my-custom-pin",
                iconAnchor: [0, 12],
                labelAnchor: [-6, 0],
                popupAnchor: [0, -36],
                html: `
                    <span style="
                        background-color: ${color};
                        width: 2rem;
                        height: 2rem;
                        display: block;
                        left: -1rem;
                        top: -1rem;
                        position: relative;
                        border-radius: 2rem 2rem 0;
                        transform: rotate(45deg);
                        border: 1px solid #FFFFFF">
                    </span>`
            });
        };

        // Add donation markers to the map with blue icon
        donationLocations.forEach(location => {
            L.marker([location.x, location.y], { icon: createIcon(donationColour) })
                .addTo(map)
                .bindPopup(`<b>Item:</b> ${location.item_type}<br><b>Amount:</b> ${location.item_amount}`);
        });

        // Add needed markers to the map with red icon
        neededLocations.forEach(location => {
            L.marker([location.x, location.y], { icon: createIcon(neededColour) })
                .addTo(map)
                .bindPopup(`<b>Item:</b> ${location.item_type}<br><b>Amount:</b> ${location.item_amount}`);
        });

        // Draw lines between connected locations
        connectedLocations.forEach(connection => {
            const xd = connection.xd; // Latitude of donation location
            const yd = connection.yd; // Longitude of donation location
            const xw = connection.xw; // Latitude of needed location
            const yw = connection.yw; // Longitude of needed location

            L.polyline([[xd, yd], [xw, yw]], {
                color: connectionColor,
                weight: 4,
                opacity: 0.8,
                smoothFactor: 1
            }).addTo(map);
        });
    })
    .catch(error => {
        console.error('Error fetching data:', error);
    });
