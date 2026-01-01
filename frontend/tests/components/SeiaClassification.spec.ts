import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import SeiaClassification from '@/components/analysis/SeiaClassification.vue';
import { useAnalysisStore } from '@/stores/analysis';
import type { ResultadoAnalisis } from '@/types';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

const mockResultadoEIA: ResultadoAnalisis = {
  id: 'analisis-eia',
  fecha_analisis: '2024-01-15T10:30:00Z',
  proyecto: { nombre: 'Proyecto EIA' },
  geometria: { type: 'Polygon', coordinates: [] },
  resultado_gis: { intersecciones: [], alertas_gis: [], area_proyecto_ha: 500, centroide: [0, 0] },
  clasificacion_seia: {
    via_ingreso_recomendada: 'EIA',
    confianza: 0.92,
    nivel_confianza: 'MUY_ALTA',
    justificacion: 'El proyecto afecta áreas protegidas del SNASPE',
    puntaje_matriz: 85.5,
  },
  triggers: [
    { letra: 'd', descripcion: 'Test', detalle: '', severidad: 'CRITICA', fundamento_legal: '', peso: 1 },
    { letra: 'b', descripcion: 'Test 2', detalle: '', severidad: 'ALTA', fundamento_legal: '', peso: 0.8 },
  ],
  alertas: [
    { id: '1', nivel: 'CRITICA', categoria: 'test', titulo: 'Test', descripcion: '', acciones_requeridas: [] },
    { id: '2', nivel: 'ALTA', categoria: 'test', titulo: 'Test 2', descripcion: '', acciones_requeridas: [] },
    { id: '3', nivel: 'MEDIA', categoria: 'test', titulo: 'Test 3', descripcion: '', acciones_requeridas: [] },
  ],
  normativa_citada: [],
  metricas: { tiempo_analisis_segundos: 2.5, tiempo_gis_ms: 150, tiempo_rag_ms: 300 },
};

const mockResultadoDIA: ResultadoAnalisis = {
  ...mockResultadoEIA,
  id: 'analisis-dia',
  clasificacion_seia: {
    via_ingreso_recomendada: 'DIA',
    confianza: 0.78,
    nivel_confianza: 'ALTA',
    justificacion: 'El proyecto no presenta impactos significativos',
    puntaje_matriz: 25.0,
  },
  triggers: [],
  alertas: [],
};

describe('SeiaClassification', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('no renderiza sin resultado', () => {
    const wrapper = mount(SeiaClassification);
    expect(wrapper.text()).toBe('');
  });

  describe('clasificacion EIA', () => {
    beforeEach(() => {
      const store = useAnalysisStore();
      store.resultado = mockResultadoEIA;
    });

    it('muestra EIA en texto grande', () => {
      const wrapper = mount(SeiaClassification, {
        global: {
          stubs: {
            ConfidenceBadge: true,
            ExportButtons: true,
          },
        },
      });

      expect(wrapper.text()).toContain('EIA');
      expect(wrapper.text()).toContain('Estudio de Impacto Ambiental');
    });

    it('aplica colores de warning para EIA', () => {
      const wrapper = mount(SeiaClassification, {
        global: {
          stubs: {
            ConfidenceBadge: true,
            ExportButtons: true,
          },
        },
      });

      const card = wrapper.find('.card');
      expect(card.classes()).toContain('border-warning');
    });

    it('muestra metricas correctas', () => {
      const wrapper = mount(SeiaClassification, {
        global: {
          stubs: {
            ConfidenceBadge: true,
            ExportButtons: true,
          },
        },
      });

      expect(wrapper.text()).toContain('85.5'); // puntaje_matriz
      expect(wrapper.text()).toContain('2');     // triggers
      expect(wrapper.text()).toContain('3');     // alertas
    });

    it('muestra justificacion', () => {
      const wrapper = mount(SeiaClassification, {
        global: {
          stubs: {
            ConfidenceBadge: true,
            ExportButtons: true,
          },
        },
      });

      expect(wrapper.text()).toContain('El proyecto afecta áreas protegidas del SNASPE');
    });

    it('muestra informacion del analisis', () => {
      const wrapper = mount(SeiaClassification, {
        global: {
          stubs: {
            ConfidenceBadge: true,
            ExportButtons: true,
          },
        },
      });

      expect(wrapper.text()).toContain('analisis-eia');
    });
  });

  describe('clasificacion DIA', () => {
    beforeEach(() => {
      const store = useAnalysisStore();
      store.resultado = mockResultadoDIA;
    });

    it('muestra DIA en texto grande', () => {
      const wrapper = mount(SeiaClassification, {
        global: {
          stubs: {
            ConfidenceBadge: true,
            ExportButtons: true,
          },
        },
      });

      expect(wrapper.text()).toContain('DIA');
      expect(wrapper.text()).toContain('Declaración de Impacto Ambiental');
    });

    it('aplica colores de success para DIA', () => {
      const wrapper = mount(SeiaClassification, {
        global: {
          stubs: {
            ConfidenceBadge: true,
            ExportButtons: true,
          },
        },
      });

      const card = wrapper.find('.card');
      expect(card.classes()).toContain('border-success');
    });

    it('muestra 0 triggers para DIA sin triggers', () => {
      const wrapper = mount(SeiaClassification, {
        global: {
          stubs: {
            ConfidenceBadge: true,
            ExportButtons: true,
          },
        },
      });

      expect(wrapper.text()).toContain('0'); // 0 triggers
    });
  });

  it('incluye ExportButtons', () => {
    const store = useAnalysisStore();
    store.resultado = mockResultadoEIA;

    const wrapper = mount(SeiaClassification, {
      global: {
        stubs: {
          ConfidenceBadge: true,
          ExportButtons: {
            template: '<div class="export-buttons-stub"></div>',
          },
        },
      },
    });

    expect(wrapper.find('.export-buttons-stub').exists()).toBe(true);
  });

  it('incluye ConfidenceBadge con props correctos', () => {
    const store = useAnalysisStore();
    store.resultado = mockResultadoEIA;

    const ConfidenceBadgeStub = {
      template: '<span class="confidence-badge-stub">{{ nivel }} - {{ porcentaje }}</span>',
      props: ['nivel', 'porcentaje'],
    };

    const wrapper = mount(SeiaClassification, {
      global: {
        stubs: {
          ConfidenceBadge: ConfidenceBadgeStub,
          ExportButtons: true,
        },
      },
    });

    const badge = wrapper.find('.confidence-badge-stub');
    expect(badge.exists()).toBe(true);
    expect(badge.text()).toContain('MUY_ALTA');
    expect(badge.text()).toContain('0.92');
  });
});
