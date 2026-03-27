import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { Plus, CreditCard as Edit, Trash2, Save, X } from 'lucide-react'

interface Room {
  id: string
  name: string
  type: string
  capacity: number
  price_per_night: number
  description: string
  amenities: string[]
  image_url: string
  status: string
}

export default function RoomManagement() {
  const [rooms, setRooms] = useState<Room[]>([])
  const [loading, setLoading] = useState(true)
  const [editingRoom, setEditingRoom] = useState<Room | null>(null)
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    loadRooms()
  }, [])

  const loadRooms = async () => {
    try {
      const { data, error } = await supabase
        .from('rooms')
        .select('*')
        .order('created_at', { ascending: false })

      if (error) throw error
      setRooms(data || [])
    } catch (error) {
      console.error('Error loading rooms:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette chambre ?')) return

    try {
      const { error } = await supabase.from('rooms').delete().eq('id', id)
      if (error) throw error
      loadRooms()
    } catch (error) {
      console.error('Error deleting room:', error)
    }
  }

  if (loading) {
    return <div className="text-center py-8">Chargement...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Gestion des Chambres</h2>
        <button
          onClick={() => {
            setEditingRoom({
              id: '',
              name: '',
              type: '',
              capacity: 2,
              price_per_night: 0,
              description: '',
              amenities: [],
              image_url: '',
              status: 'available',
            })
            setShowForm(true)
          }}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>Nouvelle chambre</span>
        </button>
      </div>

      {showForm && editingRoom && (
        <RoomForm
          room={editingRoom}
          onSave={() => {
            loadRooms()
            setShowForm(false)
            setEditingRoom(null)
          }}
          onCancel={() => {
            setShowForm(false)
            setEditingRoom(null)
          }}
        />
      )}

      <div className="grid grid-cols-1 gap-4">
        {rooms.map((room) => (
          <div key={room.id} className="card hover:shadow-lg transition-shadow">
            <div className="flex flex-col md:flex-row md:items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-xl font-bold text-gray-900">{room.name}</h3>
                  <span className="px-2 py-1 bg-primary-100 text-primary-700 rounded text-sm">
                    {room.type}
                  </span>
                  <span
                    className={`px-2 py-1 rounded text-sm ${
                      room.status === 'available'
                        ? 'bg-green-100 text-green-700'
                        : room.status === 'occupied'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}
                  >
                    {room.status}
                  </span>
                </div>
                <p className="text-gray-600 mb-2">{room.description}</p>
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <span>Capacité: {room.capacity} personnes</span>
                  <span className="font-bold text-primary-600">{room.price_per_night}€ / nuit</span>
                </div>
                {room.amenities && room.amenities.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {room.amenities.map((amenity, idx) => (
                      <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                        {amenity}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-2 mt-4 md:mt-0">
                <button
                  onClick={() => {
                    setEditingRoom(room)
                    setShowForm(true)
                  }}
                  className="btn-secondary flex items-center space-x-1"
                >
                  <Edit className="w-4 h-4" />
                  <span>Modifier</span>
                </button>
                <button onClick={() => handleDelete(room.id)} className="btn-danger flex items-center space-x-1">
                  <Trash2 className="w-4 h-4" />
                  <span>Supprimer</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function RoomForm({ room, onSave, onCancel }: { room: Room; onSave: () => void; onCancel: () => void }) {
  const [formData, setFormData] = useState(room)
  const [amenitiesInput, setAmenitiesInput] = useState(room.amenities?.join(', ') || '')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const amenitiesArray = amenitiesInput.split(',').map((a) => a.trim()).filter((a) => a)
      const data = { ...formData, amenities: amenitiesArray }

      if (room.id) {
        const { error } = await supabase.from('rooms').update(data).eq('id', room.id)
        if (error) throw error
      } else {
        const { id, ...insertData } = data
        const { error } = await supabase.from('rooms').insert(insertData)
        if (error) throw error
      }

      onSave()
    } catch (error) {
      console.error('Error saving room:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card mb-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">
        {room.id ? 'Modifier la chambre' : 'Nouvelle chambre'}
      </h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nom</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <input
              type="text"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value })}
              required
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Capacité</label>
            <input
              type="number"
              value={formData.capacity}
              onChange={(e) => setFormData({ ...formData, capacity: Number(e.target.value) })}
              required
              min={1}
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Prix par nuit (€)</label>
            <input
              type="number"
              value={formData.price_per_night}
              onChange={(e) => setFormData({ ...formData, price_per_night: Number(e.target.value) })}
              required
              min={0}
              step="0.01"
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Statut</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              className="input-field"
            >
              <option value="available">Disponible</option>
              <option value="occupied">Occupée</option>
              <option value="maintenance">Maintenance</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">URL Image</label>
            <input
              type="text"
              value={formData.image_url}
              onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
              className="input-field"
              placeholder="https://..."
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
          <textarea
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            required
            rows={3}
            className="input-field resize-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Équipements (séparés par des virgules)
          </label>
          <input
            type="text"
            value={amenitiesInput}
            onChange={(e) => setAmenitiesInput(e.target.value)}
            className="input-field"
            placeholder="WiFi, TV, Petit-déjeuner"
          />
        </div>
        <div className="flex space-x-3 pt-4">
          <button type="button" onClick={onCancel} className="btn-secondary flex-1">
            <X className="w-4 h-4 inline mr-2" />
            Annuler
          </button>
          <button type="submit" disabled={loading} className="btn-primary flex-1">
            <Save className="w-4 h-4 inline mr-2" />
            {loading ? 'Enregistrement...' : 'Enregistrer'}
          </button>
        </div>
      </form>
    </div>
  )
}
