import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ConfidenceBadge from '@/components/common/ConfidenceBadge.vue';
import type { NivelConfianza } from '@/types';

describe('ConfidenceBadge', () => {
  const niveles: Array<{ key: NivelConfianza; label: string; class: string }> = [
    { key: 'MUY_ALTA', label: 'Muy Alta', class: 'badge-success' },
    { key: 'ALTA', label: 'Alta', class: 'badge-info' },
    { key: 'MEDIA', label: 'Media', class: 'badge-warning' },
    { key: 'BAJA', label: 'Baja', class: 'badge-error' },
  ];

  describe('renderiza etiquetas correctas', () => {
    niveles.forEach(({ key, label }) => {
      it(`muestra "${label}" para nivel ${key}`, () => {
        const wrapper = mount(ConfidenceBadge, {
          props: { nivel: key },
        });

        expect(wrapper.text()).toContain(label);
      });
    });
  });

  describe('aplica clases de color correctas', () => {
    niveles.forEach(({ key, class: className }) => {
      it(`aplica ${className} para nivel ${key}`, () => {
        const wrapper = mount(ConfidenceBadge, {
          props: { nivel: key },
        });

        expect(wrapper.classes()).toContain(className);
      });
    });
  });

  describe('porcentaje', () => {
    it('no muestra porcentaje cuando no se proporciona', () => {
      const wrapper = mount(ConfidenceBadge, {
        props: { nivel: 'ALTA' },
      });

      expect(wrapper.text()).not.toContain('%');
    });

    it('muestra porcentaje cuando se proporciona', () => {
      const wrapper = mount(ConfidenceBadge, {
        props: { nivel: 'ALTA', porcentaje: 0.85 },
      });

      expect(wrapper.text()).toContain('85%');
    });

    it('redondea porcentaje correctamente', () => {
      const wrapper = mount(ConfidenceBadge, {
        props: { nivel: 'ALTA', porcentaje: 0.876 },
      });

      expect(wrapper.text()).toContain('88%');
    });

    it('muestra 0% para porcentaje 0', () => {
      const wrapper = mount(ConfidenceBadge, {
        props: { nivel: 'BAJA', porcentaje: 0 },
      });

      expect(wrapper.text()).toContain('0%');
    });

    it('muestra 100% para porcentaje 1', () => {
      const wrapper = mount(ConfidenceBadge, {
        props: { nivel: 'MUY_ALTA', porcentaje: 1 },
      });

      expect(wrapper.text()).toContain('100%');
    });
  });

  it('tiene clase badge base', () => {
    const wrapper = mount(ConfidenceBadge, {
      props: { nivel: 'ALTA' },
    });

    expect(wrapper.classes()).toContain('badge');
  });
});
