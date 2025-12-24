'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import Navbar from '@/components/marketplace/Navbar';
import Footer from '@/components/marketplace/Footer';
import productService, { CreateProductInput } from '@/services/product.service';
import artifactService from '@/services/artifact.service';
import FileUpload from '@/components/product/FileUpload';
import WorkflowUploadSection from '@/components/product/WorkflowUploadSection';
import { X, Check, AlertCircle, ArrowLeft, Save, ShieldCheck, ClipboardList, FilePlus2 } from 'lucide-react';
import Link from 'next/link';
import toast from 'react-hot-toast';

export default function UploadPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [productId, setProductId] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    long_description: '',
    type: 'workflow',
    tags: [] as string[],
    is_free: true,
    price: undefined as number | undefined,
    version: '',
    requirements: [] as string[],
    features: [] as string[],
    install_guide: '',
    workflow_file_url: '',
    thumbnail_url: '',
    preview_image_url: '',
    video_url: '',
    contact_channel: '',
    license: '',
    ownership_declaration: false,
    ownership_proof_url: '',
    screenshots: [] as string[],
    platform_requirements: {} as Record<string, any>,
    required_credentials: [] as string[],
  });

  const [tagInput, setTagInput] = useState('');
  const [requirementInput, setRequirementInput] = useState('');
  const [featureInput, setFeatureInput] = useState('');
  const [toolMeta, setToolMeta] = useState({
    manifest_name: '',
    language: '',
    entry_point: '',
    runtime: '',
    dependencies: [] as string[],
    install_command: '',
    source_repo: '',
  });
  const [integrationMeta, setIntegrationMeta] = useState({
    api_version: '',
    auth_method: '',
    platforms_supported: [] as string[],
    connector_notes: '',
    example_workflows: [] as string[],
  });
  const [credentialInput, setCredentialInput] = useState('');
  const [toolDepInput, setToolDepInput] = useState('');
  const [integrationPlatformInput, setIntegrationPlatformInput] = useState('');
  const [integrationExampleInput, setIntegrationExampleInput] = useState('');

  // Redirect if not logged in or not approved seller
  useEffect(() => {
    if (!user) {
      router.push('/login?returnTo=/seller/upload');
      return;
    }
    // Check if user is approved seller
    if (user.role !== 'seller' && user.seller_status !== 'approved') {
      if (user.seller_status === 'pending') {
        toast.error('Đơn đăng ký seller của bạn đang chờ duyệt. Vui lòng đợi admin phê duyệt.');
        router.push('/seller/apply');
      } else if (user.seller_status === 'rejected') {
        toast.error('Đơn đăng ký seller của bạn đã bị từ chối. Vui lòng kiểm tra và gửi lại đơn.');
        router.push('/seller/apply');
      } else {
        toast.error('Bạn cần đăng ký làm seller trước khi tạo sản phẩm.');
        router.push('/seller/apply');
      }
    }
  }, [user, router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    // Convert price to number if it's a number input
    let processedValue: any = value;
    if (name === 'price' && type === 'number') {
      processedValue = value === '' ? undefined : parseFloat(value);
      if (isNaN(processedValue)) {
        processedValue = undefined;
      }
    }
    
    setFormData(prev => ({ ...prev, [name]: processedValue }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
    
    // Real-time URL validation (allow local path from upload)
    if (name === 'workflow_file_url' || name === 'thumbnail_url') {
      if (value.trim()) {
        const urlPattern = /^https?:\/\/[^\s/$.?#].[^\s]*$/i;
        const isLocalPath = value.startsWith('/'); // storage service có thể trả path tương đối
        if (!urlPattern.test(value.trim()) && !isLocalPath) {
          setErrors(prev => ({ ...prev, [name]: 'URL không hợp lệ. Phải là URL đầy đủ hoặc đường dẫn file upload' }));
        } else {
          setErrors(prev => ({ ...prev, [name]: '' }));
        }
      } else {
        setErrors(prev => ({ ...prev, [name]: '' }));
      }
    }
  };

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: checked }));
  };

  const addTag = () => {
    if (tagInput.trim() && formData.tags!.length < 10) {
      setFormData(prev => ({
        ...prev,
        tags: [...(prev.tags || []), tagInput.trim()],
      }));
      setTagInput('');
    }
  };

  const removeTag = (index: number) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags!.filter((_, i) => i !== index),
    }));
  };

  const addRequirement = () => {
    if (requirementInput.trim()) {
      setFormData(prev => ({
        ...prev,
        requirements: [...(prev.requirements || []), requirementInput.trim()],
      }));
      setRequirementInput('');
    }
  };

  const removeRequirement = (index: number) => {
    setFormData(prev => ({
      ...prev,
      requirements: prev.requirements!.filter((_, i) => i !== index),
    }));
  };

  const addFeature = () => {
    if (featureInput.trim()) {
      setFormData(prev => ({
        ...prev,
        features: [...(prev.features || []), featureInput.trim()],
      }));
      setFeatureInput('');
    }
  };

  const removeFeature = (index: number) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features!.filter((_, i) => i !== index),
    }));
  };

  const addCredential = () => {
    if (credentialInput.trim()) {
      setFormData(prev => ({
        ...prev,
        required_credentials: [...(prev.required_credentials || []), credentialInput.trim()],
      }));
      setCredentialInput('');
    }
  };

  const removeCredential = (index: number) => {
    setFormData(prev => ({
      ...prev,
      required_credentials: prev.required_credentials!.filter((_, i) => i !== index),
    }));
  };

  const updateToolMeta = (key: string, value: any) => {
    setToolMeta(prev => ({ ...prev, [key]: value }));
  };
  const addToolDep = () => {
    if (toolDepInput.trim()) {
      setToolMeta(prev => ({ ...prev, dependencies: [...(prev.dependencies || []), toolDepInput.trim()] }));
      setToolDepInput('');
    }
  };
  const removeToolDep = (index: number) => {
    setToolMeta(prev => ({
      ...prev,
      dependencies: (prev.dependencies || []).filter((_, i) => i !== index),
    }));
  };

  const updateIntegrationMeta = (key: string, value: any) => {
    setIntegrationMeta(prev => ({ ...prev, [key]: value }));
  };
  const addIntegrationPlatform = () => {
    if (integrationPlatformInput.trim()) {
      setIntegrationMeta(prev => ({
        ...prev,
        platforms_supported: [...(prev.platforms_supported || []), integrationPlatformInput.trim()],
      }));
      setIntegrationPlatformInput('');
    }
  };
  const removeIntegrationPlatform = (index: number) => {
    setIntegrationMeta(prev => ({
      ...prev,
      platforms_supported: (prev.platforms_supported || []).filter((_, i) => i !== index),
    }));
  };
  const addIntegrationExample = () => {
    if (integrationExampleInput.trim()) {
      setIntegrationMeta(prev => ({
        ...prev,
        example_workflows: [...(prev.example_workflows || []), integrationExampleInput.trim()],
      }));
      setIntegrationExampleInput('');
    }
  };
  const removeIntegrationExample = (index: number) => {
    setIntegrationMeta(prev => ({
      ...prev,
      example_workflows: (prev.example_workflows || []).filter((_, i) => i !== index),
    }));
  };

  // Check what fields are missing for publishing
  const getMissingFields = (): string[] => {
    const missing: string[] = [];
    
    if (!formData.title.trim() || formData.title.length < 3) {
      missing.push('Tiêu đề');
    }
    
    if (!formData.description.trim() || formData.description.length < 10) {
      missing.push('Mô tả ngắn');
    }
    
    if (formData.type === 'workflow' && !formData.workflow_file_url?.trim()) {
      missing.push('Workflow File URL');
    }
    
    if (!formData.thumbnail_url?.trim()) {
      missing.push('Thumbnail URL');
    }

    if (!(formData as any).video_url?.trim()) {
      missing.push('Video demo');
    }

    if (!(formData as any).contact_channel?.trim()) {
      missing.push('Kênh liên hệ');
    }

    if (!formData.license?.trim()) {
      missing.push('License');
    }

    if (!formData.ownership_declaration) {
      missing.push('Xác nhận quyền sở hữu');
    }
    
    if (!formData.is_free && (!formData.price || formData.price <= 0)) {
      missing.push('Giá (cho sản phẩm trả phí)');
    }
    
    return missing;
  };

  const validate = (strict: boolean = false): boolean => {
    const newErrors: Record<string, string> = {};

    // Only validate required fields if strict mode (for publishing)
    if (strict) {
      if (!formData.title.trim()) {
        newErrors.title = 'Tiêu đề là bắt buộc';
      } else if (formData.title.length < 3) {
        newErrors.title = 'Tiêu đề phải có ít nhất 3 ký tự';
      }

      if (!formData.description.trim()) {
        newErrors.description = 'Mô tả là bắt buộc';
      } else if (formData.description.length < 10) {
        newErrors.description = 'Mô tả phải có ít nhất 10 ký tự';
      }

      if (!formData.is_free && (!formData.price || formData.price <= 0)) {
        newErrors.price = 'Giá phải lớn hơn 0 cho sản phẩm trả phí';
      }

      if (!formData.license?.trim()) {
        newErrors.license = 'Vui lòng chọn license';
      }

      if (!formData.ownership_declaration) {
        newErrors.ownership_declaration = 'Bạn cần xác nhận quyền sở hữu sản phẩm';
      }
    }

    // Always validate URL format if provided
    const urlPattern = /^https?:\/\/[^\s/$.?#].[^\s]*$/i;
    
    if (formData.workflow_file_url && formData.workflow_file_url.trim()) {
      const value = formData.workflow_file_url.trim();
      const isLocalPath = value.startsWith('/');
      if (!urlPattern.test(value) && !isLocalPath) {
        newErrors.workflow_file_url = 'URL không hợp lệ. Phải là URL đầy đủ hoặc đường dẫn file upload';
      }
    }

    if (formData.thumbnail_url && formData.thumbnail_url.trim()) {
      const value = formData.thumbnail_url.trim();
      const isLocalPath = value.startsWith('/');
      if (!urlPattern.test(value) && !isLocalPath) {
        newErrors.thumbnail_url = 'URL không hợp lệ. Phải là URL đầy đủ hoặc đường dẫn file upload';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const saveDraft = async (strict: boolean = false) => {
    // Validate URL format + required if strict
    if (!validate(strict)) {
      toast.error(strict ? 'Vui lòng điền đủ thông tin bắt buộc' : 'Vui lòng kiểm tra lại định dạng URL');
      return null;
    }

    setLoading(true);
    try {
      // Prepare data with proper types
      const submitData: CreateProductInput = {
        title: formData.title,
        description: formData.description,
        longDescription: formData.long_description?.trim() || undefined,
        type: formData.type as any,
        tags: formData.tags || [],
        isFree: formData.is_free,
        price: formData.price ? parseFloat(formData.price.toString()) : undefined,
        version: formData.version?.trim() || undefined,
        requirements: formData.requirements || [],
        features: formData.features || [],
        installGuide: formData.install_guide?.trim() || undefined,
        workflowFileUrl: formData.workflow_file_url?.trim() || undefined,
        thumbnailUrl: formData.thumbnail_url?.trim() || undefined,
        previewImageUrl: formData.preview_image_url?.trim() || undefined,
        video_url: (formData as any).video_url?.trim() || undefined as any,
        contact_channel: (formData as any).contact_channel?.trim() || undefined,
        license: formData.license?.trim() || undefined,
        ownershipDeclaration: formData.ownership_declaration,
        ownershipProofUrl: formData.ownership_proof_url?.trim() || undefined,
        screenshots: formData.screenshots || [],
        platformRequirements: formData.platform_requirements,
        required_credentials: formData.required_credentials,
        metadata: {
          ...(formData.type === 'tool' ? { tool: toolMeta } : {}),
          ...(formData.type === 'integration' ? { integration: integrationMeta } : {}),
        },
      };

      const product = productId
        ? await productService.updateProduct(productId, submitData as any)
        : await productService.createProduct(submitData);

      setProductId(product.id);

      const missingFields = getMissingFields();
      if (missingFields.length > 0) {
        toast.success(
          `Đã lưu draft. Còn thiếu: ${missingFields.join(', ')}.`,
          { duration: 5000 }
        );
      } else {
        toast.success(productId ? 'Đã lưu draft' : 'Tạo sản phẩm thành công!');
      }
      return product;
    } catch (error: any) {
      if (error.response?.data?.errors) {
        const backendErrors = error.response.data.errors;
        const newErrors: Record<string, string> = {};
        const errorMessages: string[] = [];
        
        backendErrors.forEach((err: any) => {
          if (err.path && err.path.length > 0) {
            const fieldName = err.path[0];
            const fieldLabel: Record<string, string> = {
              title: 'Tiêu đề',
              description: 'Mô tả',
              workflow_file_url: 'Workflow File URL',
              thumbnail_url: 'Thumbnail URL',
              preview_image_url: 'Preview Image URL',
              video_url: 'Video demo',
              contact_channel: 'Kênh liên hệ',
              price: 'Giá',
              type: 'Loại sản phẩm',
              license: 'License',
              ownership_declaration: 'Quyền sở hữu',
            };
            
            const label = fieldLabel[fieldName] || fieldName;
            const message = err.message || 'Giá trị không hợp lệ';
            newErrors[fieldName] = message;
            errorMessages.push(`${label}: ${message}`);
          }
        });
        
        if (Object.keys(newErrors).length > 0) {
          setErrors(newErrors);
          const errorText = errorMessages.length > 0 
            ? `Lỗi validation:\n${errorMessages.join('\n')}`
            : 'Vui lòng kiểm tra lại các trường đã đánh dấu';
          toast.error(errorText, { duration: 6000 });
          const firstErrorField = Object.keys(newErrors)[0];
          const element = document.querySelector(`[name="${firstErrorField}"]`);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            (element as HTMLElement).focus();
          }
        } else {
          const message = error.response?.data?.message || error.message || 'Lưu draft thất bại';
          toast.error(message);
        }
      } else {
        const message = error.response?.data?.message || error.message || 'Lưu draft thất bại';
        toast.error(message);
      }
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (step === 1) {
      const product = await saveDraft(false);
      if (product) {
        setStep(2);
      }
      return;
    }

    if (step === 2) {
      const product = await saveDraft(false);
      if (product) {
        setStep(3);
      }
      return;
    }

    // Step 3: finalize draft with strict validation then quay về dashboard
    const product = await saveDraft(true);
    if (product) {
      toast.success('Đã lưu đầy đủ. Bạn có thể publish sau khi admin duyệt.');
      router.push('/seller/dashboard');
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-[#0B0C10] text-gray-900 dark:text-slate-200 font-sans">
      <Navbar />

      <main className="container mx-auto px-4 py-12">
        <Link
          href="/seller/dashboard"
          className="inline-flex items-center text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Quay lại dashboard
        </Link>

        <div className="max-w-5xl mx-auto">
          <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Tải lên sản phẩm mới</h1>
            <p className="text-gray-600 dark:text-slate-400">Flow 3 bước: Thông tin → Upload file → Pháp lý & review</p>
          </header>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
            {[
              { id: 1, label: 'Thông tin cơ bản', icon: ClipboardList },
              { id: 2, label: 'Files & Upload', icon: FilePlus2 },
              { id: 3, label: 'Pháp lý & Review', icon: ShieldCheck },
            ].map((item) => {
              const active = step === item.id;
              const done = step > item.id;
              const Icon = item.icon;
              return (
                <div
                  key={item.id}
                  className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${
                    active
                      ? 'border-primary bg-primary/5 text-primary'
                      : done
                        ? 'border-green-500/50 bg-green-50 dark:bg-green-900/10 text-green-700 dark:text-green-300'
                        : 'border-gray-200 dark:border-slate-800 text-gray-700 dark:text-slate-300'
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <div>
                    <p className="text-sm font-semibold">Bước {item.id}</p>
                    <p className="text-xs opacity-80">{item.label}</p>
                  </div>
                </div>
              );
            })}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {step === 1 && (
              <>
                {/* Basic Info */}
                <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Thông tin cơ bản</h2>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                        Tiêu đề <span className="text-red-400">*</span>
                      </label>
                      <input
                        type="text"
                        name="title"
                        value={formData.title}
                        onChange={handleChange}
                        className={`w-full rounded-lg border ${
                          errors.title ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                        } bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all`}
                        placeholder="Ví dụ: Workflow tóm tắt đa nguồn"
                      />
                      {errors.title && (
                        <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {errors.title}
                        </p>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                          Loại sản phẩm <span className="text-red-400">*</span>
                        </label>
                        <select
                          name="type"
                          value={formData.type}
                          onChange={handleChange}
                          className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                        >
                          <option value="workflow">Workflow</option>
                          <option value="tool">Tool</option>
                          <option value="integration">Integration Pack</option>
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                          Phiên bản
                        </label>
                        <input
                          type="text"
                          name="version"
                          value={formData.version}
                          onChange={handleChange}
                          className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                          placeholder="Ví dụ: 1.0.0"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                        Mô tả ngắn <span className="text-red-400">*</span>
                      </label>
                      <textarea
                        name="description"
                        value={formData.description}
                        onChange={handleChange}
                        rows={3}
                        className={`w-full rounded-lg border ${
                          errors.description ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                        } bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-none`}
                        placeholder="Mô tả ngắn gọn về sản phẩm (tối thiểu 10 ký tự)"
                      />
                      {errors.description && (
                        <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {errors.description}
                        </p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                        Mô tả chi tiết
                      </label>
                      <textarea
                        name="long_description"
                        value={formData.long_description}
                        onChange={handleChange}
                        rows={5}
                        className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-none"
                        placeholder="Mô tả chi tiết về sản phẩm, cách hoạt động, use cases..."
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                          Video demo (YouTube) <span className="text-red-400">*</span>
                        </label>
                        <input
                          type="url"
                          name="video_url"
                          value={(formData as any).video_url}
                          onChange={handleChange}
                          className={`w-full rounded-lg border ${
                            errors.video_url ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                          } bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all`}
                          placeholder="https://youtube.com/..."
                        />
                        {errors.video_url && (
                          <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            {errors.video_url}
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                          Kênh liên hệ (email/Calendly/WhatsApp) <span className="text-red-400">*</span>
                        </label>
                        <input
                          type="url"
                          name="contact_channel"
                          value={(formData as any).contact_channel}
                          onChange={handleChange}
                          className={`w-full rounded-lg border ${
                            errors.contact_channel ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                          } bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all`}
                          placeholder="mailto:team@example.com hoặc https://calendly.com/..."
                        />
                        {errors.contact_channel && (
                          <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            {errors.contact_channel}
                          </p>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                        Credentials cần cho flow (n8n)
                      </label>
                      <div className="flex gap-2 mb-3">
                        <input
                          type="text"
                          value={credentialInput}
                          onChange={(e) => setCredentialInput(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addCredential())}
                          className="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-2 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                          placeholder="Ví dụ: openai, notion, slack_api_key"
                        />
                        <button
                          type="button"
                          onClick={addCredential}
                          className="px-4 py-2 bg-primary hover:bg-[#FF8559] text-white rounded-lg transition-colors"
                        >
                          Thêm
                        </button>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {formData.required_credentials!.map((item, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center gap-2 px-3 py-1 bg-gray-200 dark:bg-slate-800 rounded-lg text-sm text-gray-700 dark:text-slate-200"
                          >
                            {item}
                            <button
                              type="button"
                              onClick={() => removeCredential(index)}
                              className="text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </section>

                {/* Pricing */}
                <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Giá</h2>
                  
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        name="is_free"
                        checked={formData.is_free}
                        onChange={handleCheckboxChange}
                        className="w-5 h-5 rounded border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-900/40 text-primary focus:ring-2 focus:ring-primary"
                      />
                      <label className="text-gray-700 dark:text-slate-200">Sản phẩm miễn phí</label>
                    </div>

                    {!formData.is_free && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                          Giá (VNĐ) <span className="text-red-400">*</span>
                        </label>
                        <input
                          type="number"
                          name="price"
                          value={formData.price || ''}
                          onChange={handleChange}
                          min="0"
                          step="1000"
                          className={`w-full rounded-lg border ${
                            errors.price ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                          } bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all`}
                          placeholder="0"
                        />
                        {errors.price && (
                          <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            {errors.price}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </section>

                {/* Tags */}
                <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Tags</h2>
                  
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                      className="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-2 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                      placeholder="Thêm tag (Enter để thêm)"
                      disabled={formData.tags!.length >= 10}
                    />
                    <button
                      type="button"
                      onClick={addTag}
                      disabled={formData.tags!.length >= 10}
                      className="px-4 py-2 bg-primary hover:bg-[#FF8559] text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Thêm
                    </button>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    {formData.tags!.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center gap-2 px-3 py-1 bg-gray-200 dark:bg-slate-800 rounded-lg text-sm text-gray-700 dark:text-slate-200"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeTag(index)}
                          className="text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  <p className="mt-2 text-xs text-gray-500 dark:text-slate-500">Tối đa 10 tags ({formData.tags!.length}/10)</p>
                </section>
              </>
            )}

            {step === 2 && (
              <>
                {/* Type-specific upload */}
                {formData.type === 'workflow' && (
                  <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                    <div className="flex items-start justify-between gap-3 mb-4">
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Workflow Files & Details</h2>
                        <p className="text-sm text-gray-600 dark:text-slate-400">Upload workflow.json, README, .env.example</p>
                      </div>
                      {!productId && (
                        <span className="text-xs text-yellow-600 dark:text-yellow-300 bg-yellow-50 dark:bg-yellow-900/20 px-3 py-1 rounded-full">
                          Lưu draft ở Bước 1 để tạo productId
                        </span>
                      )}
                    </div>
                    {productId ? (
                      <WorkflowUploadSection
                        productId={productId}
                        onFilesUploaded={(files) => {
                          if (files.workflow) {
                            setFormData(prev => ({ ...prev, workflow_file_url: files.workflow! }));
                          }
                        }}
                      />
                    ) : (
                      <div className="p-4 border border-dashed border-yellow-300 rounded-lg text-sm text-yellow-700 dark:text-yellow-200 bg-yellow-50 dark:bg-yellow-900/10">
                        Vui lòng nhấn “Lưu draft & tiếp tục” ở bước 1 để tạo sản phẩm, sau đó quay lại bước này để upload file.
                      </div>
                    )}
                  </section>
                )}

                {/* Tool upload + metadata */}
                {formData.type === 'tool' && (
                  <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                    <div className="flex items-start justify-between gap-3 mb-4">
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Tool Artifacts & Metadata</h2>
                        <p className="text-sm text-gray-600 dark:text-slate-400">Upload manifest, source, test scripts và điền metadata</p>
                      </div>
                      {!productId && (
                        <span className="text-xs text-yellow-600 dark:text-yellow-300 bg-yellow-50 dark:bg-yellow-900/20 px-3 py-1 rounded-full">
                          Lưu draft ở Bước 1 để tạo productId
                        </span>
                      )}
                    </div>
                    <div className="space-y-4">
                      {productId ? (
                        <>
                          <FileUpload
                            onUpload={async (file) => {
                              const artifact = await artifactService.uploadArtifact(productId, file, 'manifest' as any);
                              const fileUrl = (artifact as any).fileUrl || (artifact as any).file_url;
                              if (fileUrl) {
                                setFormData(prev => ({ ...prev, workflow_file_url: fileUrl }));
                              }
                            }}
                            artifactType={'manifest' as any}
                            accept=".json,application/json"
                            maxSize={5}
                            label="manifest.json"
                            required
                          />
                          <FileUpload
                            onUpload={async (file) => {
                              await artifactService.uploadArtifact(productId, file, 'source_zip' as any);
                            }}
                            artifactType={'source_zip' as any}
                            accept=".zip"
                            maxSize={100}
                            label="Source code (.zip)"
                          />
                          <FileUpload
                            onUpload={async (file) => {
                              await artifactService.uploadArtifact(productId, file, 'test_scripts' as any);
                            }}
                            artifactType={'test_scripts' as any}
                            accept=".zip,.sh,.ps1,.bat,.js,.ts,.py"
                            maxSize={20}
                            label="Test/Install scripts"
                          />
                        </>
                      ) : (
                        <div className="p-4 border border-dashed border-yellow-300 rounded-lg text-sm text-yellow-700 dark:text-yellow-200 bg-yellow-50 dark:bg-yellow-900/10">
                          Lưu draft ở bước 1 để có productId rồi quay lại upload.
                        </div>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Manifest name</label>
                          <input
                            type="text"
                            value={toolMeta.manifest_name}
                            onChange={(e) => updateToolMeta('manifest_name', e.target.value)}
                            className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Ngôn ngữ</label>
                          <input
                            type="text"
                            value={toolMeta.language}
                            onChange={(e) => updateToolMeta('language', e.target.value)}
                            className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                            placeholder="javascript / python / go..."
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Entry point</label>
                          <input
                            type="text"
                            value={toolMeta.entry_point}
                            onChange={(e) => updateToolMeta('entry_point', e.target.value)}
                            className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                            placeholder="index.js / main.py ..."
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Runtime</label>
                          <input
                            type="text"
                            value={toolMeta.runtime}
                            onChange={(e) => updateToolMeta('runtime', e.target.value)}
                            className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                            placeholder="node 18+, python 3.10+..."
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Dependencies</label>
                        <div className="flex gap-2 mb-2">
                          <input
                            type="text"
                            value={toolDepInput}
                            onChange={(e) => setToolDepInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addToolDep())}
                            className="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-2 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                            placeholder="express@^4, axios..."
                          />
                          <button
                            type="button"
                            onClick={addToolDep}
                            className="px-4 py-2 bg-primary hover:bg-[#FF8559] text-white rounded-lg transition-colors"
                          >
                            Thêm
                          </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {(toolMeta.dependencies || []).map((dep, idx) => (
                            <span key={idx} className="inline-flex items-center gap-2 px-3 py-1 bg-gray-200 dark:bg-slate-800 rounded-lg text-sm text-gray-700 dark:text-slate-200">
                              {dep}
                              <button
                                type="button"
                                onClick={() => removeToolDep(idx)}
                                className="text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Install command</label>
                          <input
                            type="text"
                            value={toolMeta.install_command}
                            onChange={(e) => updateToolMeta('install_command', e.target.value)}
                            className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                            placeholder="npm install && npm run build"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Source repo (optional)</label>
                          <input
                            type="url"
                            value={toolMeta.source_repo}
                            onChange={(e) => updateToolMeta('source_repo', e.target.value)}
                            className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                            placeholder="https://github.com/org/repo"
                          />
                        </div>
                      </div>
                    </div>
                  </section>
                )}

                {/* Integration upload + metadata */}
                {formData.type === 'integration' && (
                  <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                    <div className="flex items-start justify-between gap-3 mb-4">
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Integration Artifacts & Metadata</h2>
                        <p className="text-sm text-gray-600 dark:text-slate-400">Upload connector schema / example workflow và điền metadata</p>
                      </div>
                      {!productId && (
                        <span className="text-xs text-yellow-600 dark:text-yellow-300 bg-yellow-50 dark:bg-yellow-900/20 px-3 py-1 rounded-full">
                          Lưu draft ở Bước 1 để tạo productId
                        </span>
                      )}
                    </div>
                    <div className="space-y-4">
                      {productId ? (
                        <>
                          <FileUpload
                            onUpload={async (file) => {
                              const artifact = await artifactService.uploadArtifact(productId, file, 'connector_schema' as any);
                              const fileUrl = (artifact as any).fileUrl || (artifact as any).file_url;
                              if (fileUrl) {
                                setFormData(prev => ({ ...prev, workflow_file_url: fileUrl }));
                              }
                            }}
                            artifactType={'connector_schema' as any}
                            accept=".json,application/json"
                            maxSize={5}
                            label="Connector schema (JSON)"
                            required
                          />
                          <FileUpload
                            onUpload={async (file) => {
                              await artifactService.uploadArtifact(productId, file, 'example_workflow' as any);
                            }}
                            artifactType={'example_workflow' as any}
                            accept=".json,.zip"
                            maxSize={20}
                            label="Example workflow (optional)"
                          />
                        </>
                      ) : (
                        <div className="p-4 border border-dashed border-yellow-300 rounded-lg text-sm text-yellow-700 dark:text-yellow-200 bg-yellow-50 dark:bg-yellow-900/10">
                          Lưu draft ở bước 1 để có productId rồi quay lại upload.
                        </div>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">API version</label>
                          <input
                            type="text"
                            value={integrationMeta.api_version}
                            onChange={(e) => updateIntegrationMeta('api_version', e.target.value)}
                            className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Auth method</label>
                          <input
                            type="text"
                            value={integrationMeta.auth_method}
                            onChange={(e) => updateIntegrationMeta('auth_method', e.target.value)}
                            className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                            placeholder="oauth2 / api_key / basic..."
                          />
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Platforms supported</label>
                        <div className="flex gap-2 mb-2">
                          <input
                            type="text"
                            value={integrationPlatformInput}
                            onChange={(e) => setIntegrationPlatformInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addIntegrationPlatform())}
                            className="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-2 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                            placeholder="n8n / make / zapier..."
                          />
                          <button
                            type="button"
                            onClick={addIntegrationPlatform}
                            className="px-4 py-2 bg-primary hover:bg-[#FF8559] text-white rounded-lg transition-colors"
                          >
                            Thêm
                          </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {(integrationMeta.platforms_supported || []).map((p, idx) => (
                            <span key={idx} className="inline-flex items-center gap-2 px-3 py-1 bg-gray-200 dark:bg-slate-800 rounded-lg text-sm text-gray-700 dark:text-slate-200">
                              {p}
                              <button
                                type="button"
                                onClick={() => removeIntegrationPlatform(idx)}
                                className="text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Connector notes</label>
                        <textarea
                          value={integrationMeta.connector_notes}
                          onChange={(e) => updateIntegrationMeta('connector_notes', e.target.value)}
                          rows={3}
                          className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder-text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-none"
                          placeholder="Phạm vi API, giới hạn rate, ghi chú auth..."
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">Example workflows</label>
                        <div className="flex gap-2 mb-2">
                          <input
                            type="text"
                            value={integrationExampleInput}
                            onChange={(e) => setIntegrationExampleInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addIntegrationExample())}
                            className="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-2 text-gray-900 dark:text-white placeholder-text-gray-400 dark:placeholder-text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                            placeholder="Link example workflow"
                          />
                          <button
                            type="button"
                            onClick={addIntegrationExample}
                            className="px-4 py-2 bg-primary hover:bg-[#FF8559] text-white rounded-lg transition-colors"
                          >
                            Thêm
                          </button>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {(integrationMeta.example_workflows || []).map((ex, idx) => (
                            <span key={idx} className="inline-flex items-center gap-2 px-3 py-1 bg-gray-200 dark:bg-slate-800 rounded-lg text-sm text-gray-700 dark:text-slate-200">
                              {ex}
                              <button
                                type="button"
                                onClick={() => removeIntegrationExample(idx)}
                                className="text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                              >
                                <X className="h-3 w-3" />
                              </button>
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </section>
                )}

                {/* Files & Media */}
                <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Files & Media</h2>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                        {formData.type === 'workflow' ? 'Workflow File URL' : 'Artifact/File URL'}
                      </label>
                      <input
                        type="url"
                        name="workflow_file_url"
                        value={formData.workflow_file_url}
                        onChange={handleChange}
                        className={`w-full rounded-lg border ${
                          errors.workflow_file_url ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                        } bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all`}
                        placeholder="https://example.com/artifact.json"
                      />
                      {errors.workflow_file_url && (
                        <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                          <AlertCircle className="h-3 w-3" />
                          {errors.workflow_file_url}
                        </p>
                      )}
                      <p className="mt-1 text-xs text-gray-500 dark:text-slate-500">URL đến file workflow JSON hoặc package</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200">
                          Thumbnail (upload)
                        </label>
                        {productId ? (
                          <FileUpload
                            onUpload={async (file) => {
                              const artifact = await artifactService.uploadArtifact(productId, file, 'thumbnail' as any);
                              const fileUrl = (artifact as any).fileUrl || (artifact as any).file_url;
                              if (fileUrl) {
                                setFormData(prev => ({ ...prev, thumbnail_url: fileUrl }));
                              }
                              toast.success('Upload thumbnail thành công');
                            }}
                            artifactType={'thumbnail' as any}
                            accept="image/*"
                            maxSize={10}
                            required
                          />
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-slate-500">
                            Lưu draft để lấy Product ID trước khi upload thumbnail.
                          </p>
                        )}
                        {errors.thumbnail_url && (
                          <p className="text-sm text-red-400 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            {errors.thumbnail_url}
                          </p>
                        )}
                        <p className="text-xs text-gray-500 dark:text-slate-500">Bắt buộc khi publish</p>
                        {formData.thumbnail_url && (
                          <p className="text-xs text-green-600 dark:text-green-400">
                            Đã chọn thumbnail: {formData.thumbnail_url}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </section>

                {/* Requirements */}
                <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Yêu cầu tích hợp</h2>
                  
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={requirementInput}
                      onChange={(e) => setRequirementInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addRequirement())}
                      className="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-2 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                      placeholder="Ví dụ: n8n 1.0+, OpenAI API key"
                    />
                    <button
                      type="button"
                      onClick={addRequirement}
                      className="px-4 py-2 bg-primary hover:bg-[#FF8559] text-white rounded-lg transition-colors"
                    >
                      Thêm
                    </button>
                  </div>
                  
                  <ul className="space-y-2">
                    {formData.requirements!.map((req, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm text-gray-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary" />
                        {req}
                        <button
                          type="button"
                          onClick={() => removeRequirement(index)}
                          className="ml-auto text-gray-500 dark:text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>

                {/* Features */}
                <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Tính năng chính</h2>
                  
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={featureInput}
                      onChange={(e) => setFeatureInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addFeature())}
                      className="flex-1 rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-2 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                      placeholder="Ví dụ: GPT-4 Integration, Auto-posting"
                    />
                    <button
                      type="button"
                      onClick={addFeature}
                      className="px-4 py-2 bg-primary hover:bg-[#FF8559] text-white rounded-lg transition-colors"
                    >
                      Thêm
                    </button>
                  </div>
                  
                  <ul className="space-y-2">
                    {formData.features!.map((feature, index) => (
                      <li key={index} className="flex items-center gap-2 text-sm text-gray-700 dark:text-slate-200">
                        <Check className="h-4 w-4 text-primary" />
                        {feature}
                        <button
                          type="button"
                          onClick={() => removeFeature(index)}
                          className="ml-auto text-gray-500 dark:text-slate-400 hover:text-red-500 dark:hover:text-red-400 transition-colors"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>

                {/* Install Guide */}
                <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Hướng dẫn cài đặt</h2>
                  
                  <textarea
                    name="install_guide"
                    value={formData.install_guide}
                    onChange={handleChange}
                    rows={6}
                    className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all resize-none"
                    placeholder="Hướng dẫn từng bước để cài đặt workflow/tool..."
                  />
                </section>
              </>
            )}

            {step === 3 && (
              <>
                {/* Legal & Ownership */}
                <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Pháp lý & Quyền sở hữu</h2>

                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                          License <span className="text-red-400">*</span>
                        </label>
                        <select
                          name="license"
                          value={formData.license}
                          onChange={handleChange}
                          className={`w-full rounded-lg border ${
                            errors.license ? 'border-red-500' : 'border-gray-200 dark:border-slate-700'
                          } bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all`}
                        >
                          <option value="">Chọn license</option>
                          <option value="MIT">MIT</option>
                          <option value="GPL">GPL</option>
                          <option value="Apache-2.0">Apache 2.0</option>
                          <option value="Proprietary">Proprietary</option>
                          <option value="Commercial">Commercial</option>
                        </select>
                        {errors.license && (
                          <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            {errors.license}
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-200 mb-2">
                          Proof of ownership URL (tùy chọn)
                        </label>
                        <input
                          type="url"
                          name="ownership_proof_url"
                          value={formData.ownership_proof_url}
                          onChange={handleChange}
                          className="w-full rounded-lg border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900/40 px-4 py-3 text-gray-900 dark:text-white placeholder:text-gray-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                          placeholder="https://example.com/proof.pdf"
                        />
                      </div>
                    </div>

                    <div className="flex items-start gap-3 rounded-xl border border-gray-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 p-4">
                      <input
                        type="checkbox"
                        name="ownership_declaration"
                        checked={formData.ownership_declaration}
                        onChange={handleCheckboxChange}
                        className="mt-1 w-5 h-5 rounded border-gray-300 dark:border-slate-700 text-primary focus:ring-2 focus:ring-primary"
                      />
                      <div className="space-y-1">
                        <p className="text-sm text-gray-900 dark:text-white font-semibold">Tôi cam kết có quyền phân phối sản phẩm này</p>
                        <p className="text-sm text-gray-600 dark:text-slate-400">
                          Bao gồm quyền sở hữu mã nguồn/tài nguyên, và không vi phạm bản quyền hoặc điều khoản dịch vụ của bên thứ ba.
                        </p>
                        {errors.ownership_declaration && (
                          <p className="mt-1 text-sm text-red-400 flex items-center gap-1">
                            <AlertCircle className="h-3 w-3" />
                            {errors.ownership_declaration}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </section>

                {/* Review checklist */}
                <section className="bg-gray-50 dark:bg-[#111218] border border-gray-200 dark:border-slate-800 rounded-2xl p-6">
                  <div className="flex items-center gap-2 mb-3">
                    <ShieldCheck className="h-5 w-5 text-primary" />
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Checklist trước khi submit</h2>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-700 dark:text-slate-300">
                    <p className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      Thumbnail đã có
                    </p>
                    <p className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      Workflow file / Artifact chính
                    </p>
                    <p className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      License & Ownership đã tích
                    </p>
                    <p className="flex items-center gap-2">
                      <Check className="h-4 w-4 text-primary" />
                      Không chứa credentials nhạy cảm
                    </p>
                  </div>
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">Trường còn thiếu:</p>
                    <div className="flex flex-wrap gap-2">
                      {getMissingFields().length === 0 ? (
                        <span className="px-3 py-1 rounded-full bg-green-100 text-green-700 text-xs">
                          Đã đủ điều kiện cơ bản để gửi duyệt
                        </span>
                      ) : (
                        getMissingFields().map((item, idx) => (
                          <span key={idx} className="px-3 py-1 rounded-full bg-yellow-100 text-yellow-800 text-xs">
                            {item}
                          </span>
                        ))
                      )}
                    </div>
                  </div>
                </section>
              </>
            )}

            {/* Actions */}
            <div className="flex flex-col md:flex-row gap-3">
              {step > 1 && (
                <button
                  type="button"
                  onClick={() => setStep((prev) => (prev === 1 ? 1 : (prev - 1) as any))}
                  className="md:w-40 inline-flex items-center justify-center gap-2 border border-gray-200 dark:border-slate-700 rounded-lg px-4 py-3 text-gray-800 dark:text-white hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Quay lại
                </button>
              )}

              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-primary hover:bg-[#FF8559] text-white font-semibold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Đang lưu...</span>
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    <span>
                      {step === 1 && 'Lưu draft & sang Bước 2'}
                      {step === 2 && 'Lưu & sang Bước 3'}
                      {step === 3 && 'Lưu & hoàn tất'}
                    </span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </main>

      <Footer />
    </div>
  );
}

