class Locations {
    donationLocations = [];
    neededLocations = [];

    constructor(donationLocations, neededLocations) {
        this.donationLocations = donationLocations || [];
        this.neededLocations = neededLocations || [];
    }

    getDonationLocations() {
        console.log(this.donationLocations);
        return this.donationLocations;
    }

    getNeededLocations() {
        console.log(this.neededLocations);
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

    calculateDistance(coords1, coords2) {
        const R = 6371;
        const dLat = this.degreesToRadians(coords2[0] - coords1[0]);
        const dLon = this.degreesToRadians(coords2[1] - coords1[1]);
        const a =
            Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(this.degreesToRadians(coords1[0])) * Math.cos(this.degreesToRadians(coords2[0])) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return R * c;
    }

    degreesToRadians(degrees) {
        return degrees * (Math.PI / 180);
    }
}

// Define the class as a global variable if needed
window.Locations = Locations;
