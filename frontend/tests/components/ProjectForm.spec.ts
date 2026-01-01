import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import ProjectForm from '@/components/project/ProjectForm.vue';
import { REGIONES_CHILE, COMUNAS_POR_REGION } from '@/types';

describe('ProjectForm', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('renderiza correctamente', () => {
    const wrapper = mount(ProjectForm);
    expect(wrapper.find('input[placeholder*="Proyecto"]').exists()).toBe(true);
  });

  it('muestra todas las regiones disponibles', () => {
    const wrapper = mount(ProjectForm);
    const regionSelect = wrapper.find('select');
    const options = regionSelect.findAll('option');

    // +1 por la opción "Seleccionar..."
    expect(options.length).toBe(REGIONES_CHILE.length + 1);
  });

  it('el select de comuna está deshabilitado sin región', () => {
    const wrapper = mount(ProjectForm);
    const selects = wrapper.findAll('select');
    const comunaSelect = selects[1];

    expect(comunaSelect?.attributes('disabled')).toBeDefined();
  });

  it('muestra comunas cuando se selecciona región', async () => {
    const wrapper = mount(ProjectForm);
    const selects = wrapper.findAll('select');
    const regionSelect = selects[0];

    await regionSelect?.setValue('Antofagasta');
    await wrapper.vm.$nextTick();

    const comunaSelect = selects[1];
    const comunas = COMUNAS_POR_REGION['Antofagasta'] || [];
    const options = comunaSelect?.findAll('option') || [];

    // +1 por la opción "Seleccionar..."
    expect(options.length).toBe(comunas.length + 1);
  });

  it('tiene campos de características del proyecto', () => {
    const wrapper = mount(ProjectForm);

    expect(wrapper.text()).toContain('Tipo de minería');
    expect(wrapper.text()).toContain('Fase');
    expect(wrapper.text()).toContain('Mineral principal');
    expect(wrapper.text()).toContain('Superficie');
  });

  it('tiene campos de recursos', () => {
    const wrapper = mount(ProjectForm);

    expect(wrapper.text()).toContain('Uso de agua');
    expect(wrapper.text()).toContain('Fuente de agua');
    expect(wrapper.text()).toContain('Energía');
  });

  it('tiene campos de empleo e inversión', () => {
    const wrapper = mount(ProjectForm);

    expect(wrapper.text()).toContain('Trabajadores construcción');
    expect(wrapper.text()).toContain('Trabajadores operación');
    expect(wrapper.text()).toContain('Inversión');
  });
});
