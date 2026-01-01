import { describe, it, expect, vi, beforeEach } from 'vitest';
import { apiClient, request, get, post, downloadFile } from '@/services/api';

// Mock URL y Blob APIs
const mockCreateObjectURL = vi.fn(() => 'blob:mock-url');
const mockRevokeObjectURL = vi.fn();

Object.defineProperty(window, 'URL', {
  value: {
    createObjectURL: mockCreateObjectURL,
    revokeObjectURL: mockRevokeObjectURL,
  },
});

// Mock apiClient methods
vi.spyOn(apiClient, 'request');
vi.spyOn(apiClient, 'post');

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('apiClient', () => {
    it('tiene la configuracion correcta', () => {
      expect(apiClient.defaults.timeout).toBe(120000);
      expect(apiClient.defaults.headers['Content-Type']).toBe('application/json');
    });
  });

  describe('request', () => {
    it('retorna data de la respuesta', async () => {
      const mockData = { resultado: 'test' };
      vi.mocked(apiClient.request).mockResolvedValue({ data: mockData });

      const result = await request({ method: 'GET', url: '/test' });

      expect(result).toEqual(mockData);
    });

    it('pasa la configuracion al cliente', async () => {
      vi.mocked(apiClient.request).mockResolvedValue({ data: {} });

      await request({ method: 'POST', url: '/test', data: { foo: 'bar' } });

      expect(apiClient.request).toHaveBeenCalledWith({
        method: 'POST',
        url: '/test',
        data: { foo: 'bar' },
      });
    });
  });

  describe('get', () => {
    it('hace peticion GET', async () => {
      const mockData = { items: [] };
      vi.mocked(apiClient.request).mockResolvedValue({ data: mockData });

      const result = await get('/items');

      expect(apiClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          method: 'GET',
          url: '/items',
        })
      );
      expect(result).toEqual(mockData);
    });

    it('acepta configuracion adicional', async () => {
      vi.mocked(apiClient.request).mockResolvedValue({ data: {} });

      await get('/items', { headers: { 'X-Custom': 'value' } });

      expect(apiClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          headers: { 'X-Custom': 'value' },
        })
      );
    });
  });

  describe('post', () => {
    it('hace peticion POST con datos', async () => {
      const mockData = { created: true };
      vi.mocked(apiClient.request).mockResolvedValue({ data: mockData });

      const result = await post('/items', { nombre: 'Test' });

      expect(apiClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          method: 'POST',
          url: '/items',
          data: { nombre: 'Test' },
        })
      );
      expect(result).toEqual(mockData);
    });

    it('permite datos undefined', async () => {
      vi.mocked(apiClient.request).mockResolvedValue({ data: {} });

      await post('/action');

      expect(apiClient.request).toHaveBeenCalledWith(
        expect.objectContaining({
          data: undefined,
        })
      );
    });
  });

  describe('downloadFile', () => {
    it('descarga archivo correctamente', async () => {
      const mockBlob = new Blob(['test content']);
      vi.mocked(apiClient.post).mockResolvedValue({ data: mockBlob });

      // Mock click y createElement
      const mockLink = {
        href: '',
        download: '',
        click: vi.fn(),
      };
      vi.spyOn(document, 'createElement').mockReturnValue(mockLink as unknown as HTMLAnchorElement);

      await downloadFile('/export/pdf', { data: 'test' }, 'informe.pdf');

      expect(apiClient.post).toHaveBeenCalledWith(
        '/export/pdf',
        { data: 'test' },
        { responseType: 'blob' }
      );
      expect(mockLink.download).toBe('informe.pdf');
      expect(mockLink.click).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalled();
    });
  });
});
