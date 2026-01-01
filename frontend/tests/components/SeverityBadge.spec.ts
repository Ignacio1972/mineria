import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import SeverityBadge from '@/components/common/SeverityBadge.vue';
import type { Severidad } from '@/types';

describe('SeverityBadge', () => {
  const severidades: Array<{ key: Severidad; label: string; class: string }> = [
    { key: 'CRITICA', label: 'Crítica', class: 'badge-error' },
    { key: 'ALTA', label: 'Alta', class: 'badge-warning' },
    { key: 'MEDIA', label: 'Media', class: 'badge-info' },
    { key: 'BAJA', label: 'Baja', class: 'badge-success' },
    { key: 'INFO', label: 'Info', class: 'badge-neutral' },
  ];

  describe('renderiza etiquetas correctas', () => {
    severidades.forEach(({ key, label }) => {
      it(`muestra "${label}" para severidad ${key}`, () => {
        const wrapper = mount(SeverityBadge, {
          props: { severidad: key },
        });

        expect(wrapper.text()).toBe(label);
      });
    });
  });

  describe('aplica clases de color correctas', () => {
    severidades.forEach(({ key, class: className }) => {
      it(`aplica ${className} para severidad ${key}`, () => {
        const wrapper = mount(SeverityBadge, {
          props: { severidad: key },
        });

        expect(wrapper.classes()).toContain(className);
      });
    });
  });

  describe('tamaños', () => {
    it('aplica badge-md por defecto', () => {
      const wrapper = mount(SeverityBadge, {
        props: { severidad: 'ALTA' },
      });

      expect(wrapper.classes()).toContain('badge-md');
    });

    it('aplica badge-xs cuando size es xs', () => {
      const wrapper = mount(SeverityBadge, {
        props: { severidad: 'ALTA', size: 'xs' },
      });

      expect(wrapper.classes()).toContain('badge-xs');
    });

    it('aplica badge-sm cuando size es sm', () => {
      const wrapper = mount(SeverityBadge, {
        props: { severidad: 'ALTA', size: 'sm' },
      });

      expect(wrapper.classes()).toContain('badge-sm');
    });

    it('aplica badge-lg cuando size es lg', () => {
      const wrapper = mount(SeverityBadge, {
        props: { severidad: 'ALTA', size: 'lg' },
      });

      expect(wrapper.classes()).toContain('badge-lg');
    });
  });

  it('tiene clase badge base', () => {
    const wrapper = mount(SeverityBadge, {
      props: { severidad: 'MEDIA' },
    });

    expect(wrapper.classes()).toContain('badge');
  });
});
