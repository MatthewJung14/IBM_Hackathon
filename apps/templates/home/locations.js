class Locations {
    constructor(donationLocations, neededLocations) {
        this.donationLocations = donationLocations;
        this.neededLocations = neededLocations;
    }

    getDonationLocations() {
        return this.donationLocations;
    }

    getNeededLocations() {
        return this.neededLocations;
    }
}

// Define your locations here
const donationLocations = [
    { name: "Food Bank Miami", coords: [25.7617, -80.1918] },
    { name: "Habitat for Humanity Tampa", coords: [27.9506, -82.4572] },
    { name: "Community Foundation Jacksonville", coords: [30.3322, -81.6557] }
];

const neededLocations = [
    { name: "Shelter Orlando", coords: [28.5383, -81.3792] },
    { name: "Assistance League Sarasota", coords: [27.3369, -82.5333] },
    { name: "Red Cross Gainesville", coords: [29.6516, -82.3248] }
];

// Export an instance of the Locations class
export default new Locations(donationLocations, neededLocations);