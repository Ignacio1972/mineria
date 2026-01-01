import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import AlertsPanel from '@/components/analysis/AlertsPanel.vue';
import { useAnalysisStore } from '@/stores/analysis';
import type { ResultadoAnalisis } from '@/types';

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

const mockResultadoConAlertas: ResultadoAnalisis = {
  id: 'test',
  fecha_analisis: '2024-01-15',
  proyecto: { nombre: 'Test' },
  geometria: { type: 'Polygon', coordinates: [] },
  resultado_gis: { intersecciones: [], alertas_gis: [], area_proyecto_ha: 100, centroide: [0, 0] },
  clasificacion_seia: { via_ingreso_recomendada: 'EIA', confianza: 0.9, nivel_confianza: 'ALTA', justificacion: '', puntaje_matriz: 0.8 },
  triggers: [],
  alertas: [
    { id: '1', nivel: 'CRITICA', categoria: 'areas_protegidas', titulo: 'Alerta Critica', descripcion: 'Desc 1', acciones_requeridas: ['Accion 1'] },
    { id: '2', nivel: 'CRITICA', categoria: 'glaciares', titulo: 'Otra Critica', descripcion: 'Desc 2', acciones_requeridas: [] },
    { id: '3', nivel: 'ALTA', categoria: 'recursos', titulo: 'Alerta Alta', descripcion: 'Desc 3', acciones_requeridas: [] },
    { id: '4', nivel: 'MEDIA', categoria: 'comunidades', titulo: 'Alerta Media', descripcion: 'Desc 4', acciones_requeridas: [] },
    { id: '5', nivel: 'BAJA', categoria: 'otros', titulo: 'Alerta Baja', descripcion: 'Desc 5', acciones_requeridas: [] },
  ],
  normativa_citada: [],
  metricas: { tiempo_analisis_segundos: 1, tiempo_gis_ms: 100, tiempo_rag_ms: 100 },
};

const mockResultadoSinAlertas: ResultadoAnalisis = {
  ...mockResultadoConAlertas,
  alertas: [],
};

describe('AlertsPanel', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('muestra estado vacio sin alertas', () => {
    const analysisStore = useAnalysisStore();
    analysisStore.resultado = mockResultadoSinAlertas;

    const wrapper = mount(AlertsPanel);

    expect(wrapper.text()).toContain('Sin alertas');
    expect(wrapper.text()).toContain('No se detectaron alertas');
  });

  it('muestra resumen de alertas por severidad', () => {
    const analysisStore = useAnalysisStore();
    analysisStore.resultado = mockResultadoConAlertas;

    const wrapper = mount(AlertsPanel);

    expect(wrapper.text()).toContain('2');  // 2 criticas
    expect(wrapper.text()).toContain('Críticas');
    expect(wrapper.text()).toContain('1');  // 1 alta
    expect(wrapper.text()).toContain('Altas');
  });

  it('agrupa alertas por severidad', () => {
    const analysisStore = useAnalysisStore();
    analysisStore.resultado = mockResultadoConAlertas;

    const wrapper = mount(AlertsPanel);

    // Debe haber secciones para cada severidad con alertas
    const badges = wrapper.findAll('.badge');
    expect(badges.length).toBeGreaterThan(0);
  });

  it('muestra conteo 0 para severidades sin alertas', () => {
    const analysisStore = useAnalysisStore();
    analysisStore.resultado = {
      ...mockResultadoConAlertas,
      alertas: [
        { id: '1', nivel: 'CRITICA', categoria: 'test', titulo: 'Test', descripcion: '', acciones_requeridas: [] },
      ],
    };

    const wrapper = mount(AlertsPanel);

    // Debe mostrar la seccion de criticas con conteo 1
    expect(wrapper.text()).toContain('Críticas');
    expect(wrapper.text()).toContain('1');
    // Otras severidades muestran 0
    expect(wrapper.text()).toContain('0');
  });

  it('muestra badges con conteo correcto', () => {
    const analysisStore = useAnalysisStore();
    analysisStore.resultado = mockResultadoConAlertas;

    const wrapper = mount(AlertsPanel);

    // Buscar badges que contengan numeros
    const text = wrapper.text();
    expect(text).toContain('2'); // 2 criticas
    expect(text).toContain('1'); // 1 alta, 1 media, 1 baja
  });

  it('renderiza AlertCard para cada alerta', async () => {
    const analysisStore = useAnalysisStore();
    analysisStore.resultado = mockResultadoConAlertas;

    const wrapper = mount(AlertsPanel, {
      global: {
        stubs: {
          AlertCard: {
            template: '<div class="alert-card-stub">{{ alerta.titulo }}</div>',
            props: ['alerta'],
          },
          EmptyState: {
            template: '<div class="empty-state-stub"></div>',
            props: ['titulo', 'descripcion', 'icono'],
          },
        },
      },
    });

    const alertCards = wrapper.findAll('.alert-card-stub');
    expect(alertCards.length).toBe(5);
  });

  it('ordena severidades correctamente (criticas primero)', () => {
    const analysisStore = useAnalysisStore();
    analysisStore.resultado = mockResultadoConAlertas;

    const wrapper = mount(AlertsPanel);

    const text = wrapper.text();
    const criticasPos = text.indexOf('Críticas');
    const altasPos = text.indexOf('Altas');
    const mediasPos = text.indexOf('Medias');

    expect(criticasPos).toBeLessThan(altasPos);
    expect(altasPos).toBeLessThan(mediasPos);
  });
});
