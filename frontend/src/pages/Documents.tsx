import React, { useEffect, useState } from 'react';
import { useApi } from '../hooks/useApi';
import { useAuth } from '../contexts/AuthContext';
import { format, parseISO } from 'date-fns';
import { FileText, Download, CheckCircle, Clock, ShieldAlert } from 'lucide-react';

const Documents = () => {
  const { request, loading } = useApi();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'company' | 'vault'>('company');
  const [companyDocs, setCompanyDocs] = useState<any[]>([]);
  const [personalDocs, setPersonalDocs] = useState<any[]>([]);

  const fetchDocs = async () => {
    try {
      if (activeTab === 'company') {
        const res = await request('/documents/company');
        setCompanyDocs(res);
      } else {
        const res = await request('/documents/vault');
        setPersonalDocs(res);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, [activeTab, request]);

  const handleAcknowledge = async (id: string) => {
    try {
      await request(`/documents/${id}/acknowledge`, { method: 'POST' });
      fetchDocs();
    } catch (err) {
      alert("Failed to acknowledge document");
    }
  };

  const renderDocs = (docs: any[], isCompany: boolean) => {
    if (loading) return <div className="p-xl text-center"><span className="spinner"></span></div>;
    if (docs.length === 0) return (
      <div className="empty-state py-2xl">
        <FileText size={48} className="text-muted/50 mb-md" />
        <div className="empty-state-title">No documents found</div>
        <div className="empty-state-text">Check back later for updates.</div>
      </div>
    );

    return (
      <div className="grid grid-auto">
        {docs.map(doc => (
          <div key={doc.id} className="card doc-card animate-scale group">
            <div className="card-body flex-col gap-sm relative h-full">
              <div className="flex justify-between items-start">
                <div 
                  style={{ 
                    width: '48px', 
                    height: '48px', 
                    borderRadius: '12px', 
                    background: 'linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(0, 240, 255, 0.02))', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center' 
                  }}
                >
                  <FileText className="text-accent" />
                </div>
                {isCompany && doc.requires_ack && !doc.acknowledged && (
                  <span className="badge badge-pending animate-pulse">Action Required</span>
                )}
                {isCompany && doc.requires_ack && doc.acknowledged && (
                  <span className="badge badge-approved">
                    <CheckCircle size={12} style={{ marginRight: '4px' }} /> Ack'd
                  </span>
                )}
              </div>
              
              <div className="mt-md flex-1">
                <h3 className="font-bold text-lg leading-tight mb-xs text-white" style={{ margin: 0 }}>{doc.title}</h3>
                <p className="text-sm text-muted line-clamp-2" style={{ marginTop: '4px' }}>{doc.description}</p>
              </div>

              <div className="mt-lg pt-md border-t border-white/5 flex justify-between items-center">
                <div className="text-xs text-muted font-medium uppercase tracking-wider">
                  {format(parseISO(doc.created_at), 'MMM d, yyyy')}
                </div>
                <div className="flex gap-sm">
                  {isCompany && doc.requires_ack && !doc.acknowledged && (
                    <button 
                      onClick={() => handleAcknowledge(doc.id)}
                      className="btn btn-sm btn-primary rounded-full shadow-glow"
                    >
                      Acknowledge
                    </button>
                  )}
                  <a 
                    href={doc.storage_url} 
                    target="_blank" 
                    rel="noreferrer" 
                    className="btn btn-icon btn-secondary rounded-full"
                    style={{ transition: 'background-color 0.2s, opacity 0.2s', opacity: 0.8 }}
                    onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                    onMouseLeave={(e) => e.currentTarget.style.opacity = '0.8'}
                  >
                    <Download size={16} />
                  </a>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="animate-in stagger">
      <div className="page-header">
        <div>
          <h1 className="page-title text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">Documents</h1>
          <p className="page-description">Company policies and your personal vault</p>
        </div>
      </div>

      <div className="tabs glass-tabs mb-xl">
        <button 
          className={`tab ${activeTab === 'company' ? 'active' : ''}`}
          onClick={() => setActiveTab('company')}
        >
          Company Policies
        </button>
        <button 
          className={`tab ${activeTab === 'vault' ? 'active' : ''}`}
          onClick={() => setActiveTab('vault')}
        >
          My Vault
        </button>
      </div>

      {activeTab === 'company' ? renderDocs(companyDocs, true) : renderDocs(personalDocs, false)}
    </div>
  );
};

export default Documents;
