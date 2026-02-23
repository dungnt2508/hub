"use client";

import GlassContainer from "@/components/ui/GlassContainer";
import { Users, Search, Mail, Phone, Calendar, MoreHorizontal, User, Tag } from "lucide-react";
import { cn } from "@/lib/utils";
import { useQuery } from "@tanstack/react-query";
import { apiService, Contact } from "@/lib/apiService";
import { useState } from "react";

export default function ContactsPage() {
    const [searchQuery, setSearchQuery] = useState("");

    const { data: contacts = [], isLoading } = useQuery({
        queryKey: ["contacts"],
        queryFn: () => apiService.listContacts(),
    });

    const filteredContacts = contacts.filter(c =>
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.phone?.includes(searchQuery)
    );

    return (
        <div className="h-full flex flex-col space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex flex-col">
                    <h1 className="text-2xl font-black text-white">Contacts</h1>
                    <p className="text-xs text-gray-500 font-bold uppercase tracking-[0.2em] mt-1">Customer & Lead Management</p>
                </div>
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                    <input
                        type="text"
                        placeholder="Search contacts..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-xs text-white focus:outline-none focus:border-accent/50 transition-all w-64"
                    />
                </div>
            </div>

            <GlassContainer className="flex-1 overflow-hidden flex flex-col bg-white/5 border-white/5 p-0">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="text-[10px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5 bg-white/[0.02]">
                                <th className="py-4 pl-6 font-black w-12">#</th>
                                <th className="py-4 font-black">Customer</th>
                                <th className="py-4 font-black">Contact Info</th>
                                <th className="py-4 font-black">Status</th>
                                <th className="py-4 font-black">Tags</th>
                                <th className="py-4 font-black">Last Active</th>
                                <th className="py-4 font-black text-right pr-6">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {isLoading ? (
                                <tr>
                                    <td colSpan={7} className="py-8 text-center text-xs text-gray-500">Loading contacts...</td>
                                </tr>
                            ) : filteredContacts.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="py-8 text-center text-xs text-gray-500">No contacts found.</td>
                                </tr>
                            ) : filteredContacts.map((contact, idx) => (
                                <tr key={contact.id} className="group hover:bg-white/[0.02] transition-colors">
                                    <td className="py-4 pl-6 text-xs text-gray-600 font-mono">{idx + 1}</td>
                                    <td className="py-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 flex items-center justify-center text-xs font-bold text-white border border-white/10">
                                                {contact.name.charAt(0)}
                                            </div>
                                            <div>
                                                <div className="text-sm font-bold text-white">{contact.name}</div>
                                                <div className="text-[10px] text-gray-500 uppercase tracking-wide">{contact.id.slice(0, 8)}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="py-4">
                                        <div className="flex flex-col gap-1">
                                            <div className="flex items-center gap-2 text-xs text-gray-300">
                                                <Mail className="w-3 h-3 text-gray-500" /> {contact.email}
                                            </div>
                                            {contact.phone && (
                                                <div className="flex items-center gap-2 text-xs text-gray-400">
                                                    <Phone className="w-3 h-3 text-gray-500" /> {contact.phone}
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                    <td className="py-4">
                                        <span className={cn(
                                            "px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest border",
                                            contact.status === "active" ? "bg-green-500/10 border-green-500/20 text-green-500" :
                                                contact.status === "lead" ? "bg-accent/10 border-accent/20 text-accent" :
                                                    "bg-white/5 border-white/10 text-gray-500"
                                        )}>
                                            {contact.status}
                                        </span>
                                    </td>
                                    <td className="py-4">
                                        <div className="flex gap-1 flex-wrap">
                                            {contact.tags?.map((tag, i) => (
                                                <span key={i} className="px-1.5 py-0.5 rounded bg-white/5 text-[9px] text-gray-400 border border-white/5">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="py-4 text-xs text-gray-500 font-medium">
                                        {new Date(contact.last_active).toLocaleDateString()}
                                    </td>
                                    <td className="py-4 text-right pr-6">
                                        <button className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white">
                                            <MoreHorizontal className="w-4 h-4" />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </GlassContainer>
        </div>
    );
}
