import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';

// Hoist mock instances so they're available when mocks are evaluated
const { mockMapInstance, mockViewInstance } = vi.hoisted(() => {
  const mockViewInstance = {
    getCenter: vi.fn(() => [0, 0]),
    getZoom: vi.fn(() => 6),
    on: vi.fn(),
    animate: vi.fn(),
  };

  const mockMapInstance = {
    addOverlay: vi.fn(),
    getLayers: vi.fn(() => ({
      insertAt: vi.fn(),
    })),
    getView: vi.fn(() => mockViewInstance),
    on: vi.fn(),
    addInteraction: vi.fn(),
    removeInteraction: vi.fn(),
    forEachFeatureAtPixel: vi.fn(),
  };

  return { mockMapInstance, mockViewInstance };
});

// Mock OpenLayers modules
vi.mock('ol', () => ({
  Map: vi.fn(() => mockMapInstance),
  View: vi.fn(() => mockViewInstance),
  Overlay: vi.fn(() => ({
    setPosition: vi.fn(),
  })),
}));

vi.mock('ol/layer', () => ({
  Tile: vi.fn(() => ({
    setVisible: vi.fn(),
    setOpacity: vi.fn(),
  })),
  Vector: vi.fn(() => ({
    setVisible: vi.fn(),
  })),
}));

vi.mock('ol/source', () => ({
  OSM: vi.fn(),
  XYZ: vi.fn(),
  TileWMS: vi.fn(),
  Vector: vi.fn(() => ({
    clear: vi.fn(),
    getFeatures: vi.fn(() => []),
    addFeature: vi.fn(),
  })),
}));

vi.mock('ol/interaction', () => ({
  Draw: vi.fn(() => ({
    on: vi.fn(),
  })),
  Modify: vi.fn(() => ({
    on: vi.fn(),
  })),
}));

vi.mock('ol/style', () => ({
  Style: vi.fn(),
  Fill: vi.fn(),
  Stroke: vi.fn(),
}));

vi.mock('ol/proj', () => ({
  fromLonLat: vi.fn((coords) => coords),
  toLonLat: vi.fn((coords) => coords),
}));

vi.mock('ol/format/GeoJSON', () => ({
  default: vi.fn(() => ({
    writeGeometryObject: vi.fn(() => ({
      type: 'Polygon',
      coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    })),
    readFeature: vi.fn(() => ({
      getGeometry: vi.fn(),
    })),
  })),
}));

// Mock child components
vi.mock('@/components/map/MapControls.vue', () => ({
  default: {
    name: 'MapControls',
    template: '<div class="map-controls-mock"></div>',
  },
}));

vi.mock('@/components/map/DrawTools.vue', () => ({
  default: {
    name: 'DrawTools',
    template: '<div class="draw-tools-mock"></div>',
  },
}));

// Mock stores
vi.mock('@/stores/map', () => ({
  useMapStore: vi.fn(() => ({
    capas: [
      { id: 'areas_protegidas', nombre: 'Areas Protegidas', visible: false, opacidad: 0.7 },
    ],
    mapaBase: 'osm',
    centro: [-70.6483, -33.4569],
    zoom: 6,
    herramientaDibujo: null,
    setCentro: vi.fn(),
    setZoom: vi.fn(),
    desactivarEdicion: vi.fn(),
    cargarCapasDesdeAPI: vi.fn(),
  })),
}));

vi.mock('@/stores/project', () => ({
  useProjectStore: vi.fn(() => ({
    geometria: null,
    actualizarGeometria: vi.fn(),
  })),
}));

// Import component after mocks are set up
import MapContainer from '@/components/map/MapContainer.vue';

describe('MapContainer', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should render the map container', async () => {
    const wrapper = mount(MapContainer, {
      global: {
        stubs: {
          MapControls: true,
          DrawTools: true,
        },
      },
    });

    await flushPromises();

    expect(wrapper.find('.relative.w-full.h-full').exists()).toBe(true);
  });

  it('should render MapControls component', async () => {
    const wrapper = mount(MapContainer, {
      global: {
        stubs: {
          MapControls: true,
          DrawTools: true,
        },
      },
    });

    await flushPromises();

    expect(wrapper.findComponent({ name: 'MapControls' }).exists()).toBe(true);
  });

  it('should render DrawTools component', async () => {
    const wrapper = mount(MapContainer, {
      global: {
        stubs: {
          MapControls: true,
          DrawTools: true,
        },
      },
    });

    await flushPromises();

    expect(wrapper.findComponent({ name: 'DrawTools' }).exists()).toBe(true);
  });

  it('should have tooltip element hidden by default', async () => {
    const wrapper = mount(MapContainer, {
      global: {
        stubs: {
          MapControls: true,
          DrawTools: true,
        },
      },
    });

    await flushPromises();

    const tooltip = wrapper.find('[style*="display: none"]');
    expect(tooltip.exists()).toBe(true);
    expect(tooltip.classes()).toContain('bg-base-100');
  });

  it('should initialize with correct structure', async () => {
    const wrapper = mount(MapContainer, {
      global: {
        stubs: {
          MapControls: true,
          DrawTools: true,
        },
      },
    });

    await flushPromises();

    // Check that map ref div exists
    const mapDiv = wrapper.find('div > div');
    expect(mapDiv.exists()).toBe(true);
    expect(mapDiv.classes()).toContain('w-full');
    expect(mapDiv.classes()).toContain('h-full');
  });

});
