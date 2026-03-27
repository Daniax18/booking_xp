import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { format } from 'date-fns'
import { fr } from 'date-fns/locale'
import { Users as UsersIcon, Mail, Shield } from 'lucide-react'

interface User {
  id: string
  email: string
  full_name: string
  role: string
  created_at: string
}

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const { data, error } = await supabase
        .from('users')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) throw error
      setUsers(data || [])
    } catch (error) {
      console.error('Error loading users:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      const { error } = await supabase
        .from('users')
        .update({ role: newRole })
        .eq('id', userId)

      if (error) throw error
      loadUsers()
    } catch (error) {
      console.error('Error updating user role:', error)
    }
  }

  const filteredUsers = filter === 'all'
    ? users
    : users.filter(u => u.role === filter)

  const stats = {
    total: users.length,
    clients: users.filter(u => u.role === 'client').length,
    admins: users.filter(u => u.role === 'admin').length,
  }

  if (loading) {
    return <div className="text-center py-8">Chargement...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Gestion des Utilisateurs</h2>
          <div className="flex space-x-4 mt-2 text-sm">
            <span className="text-gray-600">Total: <span className="font-bold">{stats.total}</span></span>
            <span className="text-gray-600">Clients: <span className="font-bold">{stats.clients}</span></span>
            <span className="text-gray-600">Admins: <span className="font-bold">{stats.admins}</span></span>
          </div>
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="input-field w-48"
        >
          <option value="all">Tous</option>
          <option value="client">Clients</option>
          <option value="admin">Admins</option>
        </select>
      </div>

      <div className="space-y-4">
        {filteredUsers.map((user) => (
          <div key={user.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
                    <UsersIcon className="w-6 h-6 text-primary-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{user.full_name}</h3>
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <Mail className="w-4 h-4" />
                      <span>{user.email}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-4 text-sm">
                  <div>
                    <p className="text-gray-500">Inscrit le</p>
                    <p className="font-medium">
                      {format(new Date(user.created_at), 'dd MMM yyyy', { locale: fr })}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500">ID</p>
                    <p className="font-mono text-xs">{user.id.substring(0, 8)}...</p>
                  </div>
                </div>
              </div>

              <div className="md:ml-6 mt-4 md:mt-0 flex items-center space-x-3">
                <Shield className="w-5 h-5 text-gray-400" />
                <select
                  value={user.role}
                  onChange={(e) => handleRoleChange(user.id, e.target.value)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium border-none cursor-pointer ${
                    user.role === 'admin'
                      ? 'bg-purple-100 text-purple-800'
                      : 'bg-blue-100 text-blue-800'
                  }`}
                >
                  <option value="client">Client</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
          </div>
        ))}

        {filteredUsers.length === 0 && (
          <div className="card text-center py-12">
            <UsersIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Aucun utilisateur trouvé</p>
          </div>
        )}
      </div>
    </div>
  )
}
