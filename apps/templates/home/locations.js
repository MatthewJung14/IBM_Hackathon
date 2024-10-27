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

    addDonationLocation(location) {
        this.donationLocations.push(location);
    }

    addNeededLocation(location) {
        this.neededLocations.push(location);
    }

    findLocationByName(name) {
        return [
            ...this.donationLocations.filter(loc => loc.name === name),
            ...this.neededLocations.filter(loc => loc.name === name),
        ];
    }

    // Example of a function to calculate distance between two points
    calculateDistance(coords1, coords2) {
        const R = 6371; // Radius of the Earth in km
        const dLat = this.degreesToRadians(coords2[0] - coords1[0]);
        const dLon = this.degreesToRadians(coords2[1] - coords1[1]);
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(this.degreesToRadians(coords1[0])) * Math.cos(this.degreesToRadians(coords2[0])) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c; // Distance in km
    }

    degreesToRadians(degrees) {
        return degrees * (Math.PI / 180);
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