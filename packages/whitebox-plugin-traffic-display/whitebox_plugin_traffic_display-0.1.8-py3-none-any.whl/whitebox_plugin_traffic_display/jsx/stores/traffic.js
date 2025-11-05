import { create } from "zustand";

const { api } = Whitebox;

const getTrafficLabel = (traffic) => {
  // Create label with callsign (Tail or Reg) and altitude
  const callsign = traffic.Tail || traffic.Reg || traffic.Icao_addr;
  const altitude = traffic.Alt ? traffic.Alt : "N/A";
  const speed = traffic.Speed ? traffic.Speed : "N/A";
  return `${callsign}\n${altitude}ft\n${speed}kt`;
};

const createPositionTrackerSlice = (set, get) => ({
  positionData: [],

  addPositionsForEntities: (positionEntries) => {
    // entity, position, timestamp

    set((state) => {
      const positionData = {...state.positionData};

      for (const entry of positionEntries) {
        const [ entity, position, timestamp ] = entry;

        const positionValid = position.latitude && position.longitude;
        if (!positionValid) continue;

        const existingEntityPositionData = positionData[entity];
        const newEntityPositionData = [...(existingEntityPositionData || [])];

        newEntityPositionData.push({
          ...position,
          timestamp,
        });
        positionData[entity] = newEntityPositionData;
      }

      return { positionData };
    });
  },

  removePositionsForEntities: (entities) => {
    set((state) => {
      const positionData = {...state.positionData};

      for (const entity of entities) {
        delete positionData[entity];
      }

      return { positionData };
    })
  },
});

const createTrafficSlice = (set, get) => ({
  staleTrafficTimeout: 1000 * 10, // Clear stale traffic after 10 seconds
  staleTrafficRemovalInterval: 1000 * 1, // Check for stale traffic every 1 seconds
  trafficData: [],
  trafficMarkers: {},

  addTrafficData: (newData) => {
    const positionData = [];
    const timestamp = Date.now();

    set((state) => {
      const trafficData = [...state.trafficData];

      const existingTrafficIdentifiers = trafficData.map(
        ({ Icao_addr }) => Icao_addr
      );

      for (const entry of newData) {
        const tracked = existingTrafficIdentifiers.includes(entry.Icao_addr);

        if (!tracked) {
          trafficData.push({ ...entry, lastUpdate: Date.now() });
          continue;
        }

        const existingEntry = trafficData.find(
          (traffic) => traffic.Icao_addr === entry.Icao_addr
        );
        Object.assign(existingEntry, { ...entry, lastUpdate: Date.now() });

        // Prepare positions for bulk update
        const position = {
          latitude: entry.Lat,
          longitude: entry.Lng,
        };
        positionData.push([entry.Icao_addr, position, timestamp]);
      }

      return { trafficData };
    });

    get().addPositionsForEntities(positionData);
  },

  removeStaleTrafficData: () => {
    let staleEntities;

    set((state) => {
      const currentTime = Date.now();
      const prevTrackedEntities = state.trafficData.map(
          ({ Icao_addr }) => Icao_addr
      );

      const newTrafficData = state.trafficData.filter(
        (traffic) =>
          currentTime - traffic.lastUpdate <= state.staleTrafficTimeout
      );
      const updatedTrackedEntities = newTrafficData.map(
          ({ Icao_addr }) => Icao_addr
      );
      staleEntities = prevTrackedEntities.filter(
          (entity) => !updatedTrackedEntities.includes(entity)
      );

      return { trafficData: newTrafficData };
    });

    get().removePositionsForEntities(staleEntities);
  },

  renderTrafficData: () => {
    set((state) => {
      const newTrafficMarkers = { ...state.trafficMarkers };
      const trafficIdsOnMap = new Set(Object.keys(newTrafficMarkers));

      const currentTrafficIds = new Set(
        state.trafficData.map((traffic) => traffic.Icao_addr.toString())
      );

      // Remove markers that are no longer in traffic state
      for (const renderedId of trafficIdsOnMap) {
        if (!currentTrafficIds.has(renderedId)) {
          delete newTrafficMarkers[renderedId];
        }
      }

      // Add or update markers for current traffic
      for (const traffic of state.trafficData) {
        const trafficId = traffic.Icao_addr.toString();
        const label = getTrafficLabel(traffic);
        const iconURL =
          api.getStaticUrl() + "whitebox_plugin_traffic_display/assets/plane.svg";

        if (!trafficIdsOnMap.has(trafficId)) {
          newTrafficMarkers[trafficId] = {
            lat: traffic.Lat,
            lon: traffic.Lng,
            bearing: traffic.Track,
            iconUrl: iconURL,
            label: label,
          };

        } else {
          newTrafficMarkers[trafficId] = {
            ...newTrafficMarkers[trafficId],
            lat: traffic.Lat,
            lon: traffic.Lng,
            bearing: traffic.Track,
            label: label,
          }
        }
      }

      return { trafficMarkers: newTrafficMarkers };
    });
  },

  updateTraffic(data) {
    const trafficMessages = data.messages;
    if (!trafficMessages.length) return;

    get().addTrafficData(trafficMessages);
    get().renderTrafficData();
  },

  removeStaleTraffic() {
    get().removeStaleTrafficData();
    get().renderTrafficData();
  },
});

const useTrafficStore = create((...a) => ({
  ...createPositionTrackerSlice(...a),
  ...createTrafficSlice(...a),
}));

export { getTrafficLabel, useTrafficStore };
export default useTrafficStore;
