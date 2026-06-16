import { useState, useEffect } from "react";
import { Plus, X, GripVertical, Mail, Settings, Save, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardContent } from "../ui/Card";

export default function UserDataCollectionPanel() {
  const [enabled, setEnabled] = useState(false);
  const [customFields, setCustomFields] = useState([]);
  const [timing, setTiming] = useState("after_first_message");
  const [message, setMessage] = useState("Please share your details:");
  const [notificationEmails, setNotificationEmails] = useState([]);
  const [emailInput, setEmailInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fieldTypes = [
    { value: "text", label: "Text" },
    { value: "email", label: "Email" },
    { value: "phone", label: "Phone" },
    { value: "number", label: "Number" },
    { value: "textarea", label: "Long Text" },
    { value: "url", label: "URL" }
  ];

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/settings/data-collection", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setEnabled(data.enabled || false);
        setCustomFields(data.custom_fields || []);
        setTiming(data.data_collection_timing || "after_first_message");
        setMessage(data.data_collection_message || "Please share your details:");
        setNotificationEmails(data.notification_emails || []);
      }
    } catch (err) {
      setError("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const addField = () => {
    const newField = {
      field_id: `field_${Date.now()}`,
      label: "New Field",
      field_type: "text",
      placeholder: "",
      required: false,
      order: customFields.length
    };
    setCustomFields([...customFields, newField]);
  };

  const removeField = (index) => {
    const updated = customFields.filter((_, i) => i !== index);
    // Reorder
    updated.forEach((field, i) => field.order = i);
    setCustomFields(updated);
  };

  const updateField = (index, key, value) => {
    const updated = [...customFields];
    updated[index][key] = value;
    setCustomFields(updated);
  };

  const moveField = (index, direction) => {
    if (
      (direction === "up" && index === 0) ||
      (direction === "down" && index === customFields.length - 1)
    ) {
      return;
    }

    const updated = [...customFields];
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    [updated[index], updated[targetIndex]] = [updated[targetIndex], updated[index]];
    
    // Update order
    updated.forEach((field, i) => field.order = i);
    setCustomFields(updated);
  };

  const addEmail = () => {
    const trimmed = emailInput.trim();
    if (trimmed && !notificationEmails.includes(trimmed)) {
      setNotificationEmails([...notificationEmails, trimmed]);
      setEmailInput("");
    }
  };

  const removeEmail = (email) => {
    setNotificationEmails(notificationEmails.filter(e => e !== email));
  };

  const saveSettings = async () => {
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/settings/data-collection", {
        method: "PUT",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          enabled,
          custom_fields: customFields,
          data_collection_timing: timing,
          data_collection_message: message,
          notification_emails: notificationEmails
        })
      });

      if (res.ok) {
        setSuccess("Settings saved successfully!");
        setTimeout(() => setSuccess(""), 3000);
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to save settings");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <div className="text-center py-4">Loading...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold text-lg">User Data Collection</h3>
          </div>
          <label className="flex items-center gap-3 cursor-pointer bg-white px-4 py-2 rounded-lg border-2 border-purple-200 hover:border-purple-400 transition">
            <span className="text-sm font-medium text-gray-700">Enable Collection</span>
            <div className="relative">
              <input
                type="checkbox"
                checked={enabled}
                onChange={(e) => setEnabled(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
            </div>
          </label>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded p-3 flex items-center gap-2 text-red-800 text-sm">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}
        
        {success && (
          <div className="bg-green-50 border border-green-200 rounded p-3 text-green-800 text-sm">
            {success}
          </div>
        )}

        {/* Form Fields */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700">Form Fields</label>
            <button
              onClick={addField}
              className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700 transition"
            >
              <Plus className="w-4 h-4" />
              Add Field
            </button>
          </div>

          {customFields.length === 0 && (
            <div className="text-center py-6 text-gray-500 text-sm border-2 border-dashed rounded-lg">
              No fields added yet. Click "Add Field" to start building your form.
            </div>
          )}

          {customFields.map((field, index) => (
            <div
              key={field.field_id}
              className="bg-white border border-gray-200 rounded-lg p-4 space-y-3"
            >
              <div className="flex items-center gap-2">
                <div className="flex flex-col gap-1">
                  <button
                    onClick={() => moveField(index, "up")}
                    disabled={index === 0}
                    className="text-gray-400 hover:text-gray-600 disabled:opacity-30"
                    title="Move up"
                  >
                    ▲
                  </button>
                  <button
                    onClick={() => moveField(index, "down")}
                    disabled={index === customFields.length - 1}
                    className="text-gray-400 hover:text-gray-600 disabled:opacity-30"
                    title="Move down"
                  >
                    ▼
                  </button>
                </div>
                
                <GripVertical className="w-5 h-5 text-gray-400" />
                
                <div className="flex-1 grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    value={field.label}
                    onChange={(e) => updateField(index, "label", e.target.value)}
                    placeholder="Field Label"
                    className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500 text-sm"
                  />
                  <select
                    value={field.field_type}
                    onChange={(e) => updateField(index, "field_type", e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500 text-sm"
                  >
                    {fieldTypes.map(type => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>

                <button
                  onClick={() => removeField(index)}
                  className="p-2 text-red-500 hover:bg-red-50 rounded transition"
                  title="Remove field"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-center gap-3 ml-14">
                <input
                  type="text"
                  value={field.placeholder || ""}
                  onChange={(e) => updateField(index, "placeholder", e.target.value)}
                  placeholder="Placeholder text (optional)"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500 text-sm"
                />
                <label className="flex items-center gap-2 cursor-pointer text-sm">
                  <input
                    type="checkbox"
                    checked={field.required}
                    onChange={(e) => updateField(index, "required", e.target.checked)}
                    className="w-4 h-4"
                  />
                  Required
                </label>
              </div>
            </div>
          ))}
        </div>

        {/* Timing */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            When to show form?
          </label>
          <select
            value={timing}
            onChange={(e) => setTiming(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500"
          >
            <option value="immediately">Immediately when widget loads</option>
            <option value="after_first_message">After first message exchange</option>
          </select>
        </div>

        {/* Message */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Form Message
          </label>
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500"
            placeholder="Message shown above the form"
          />
        </div>

        {/* Notification Emails */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
            <Mail className="w-4 h-4" />
            Email Notifications
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="email"
              value={emailInput}
              onChange={(e) => setEmailInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && addEmail()}
              placeholder="admin@company.com"
              className="flex-1 px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-purple-500"
            />
            <button
              onClick={addEmail}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 transition"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
          
          {notificationEmails.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {notificationEmails.map(email => (
                <span
                  key={email}
                  className="flex items-center gap-2 px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm"
                >
                  {email}
                  <button
                    onClick={() => removeEmail(email)}
                    className="hover:text-purple-900"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Save Button */}
        <button
          onClick={saveSettings}
          disabled={saving}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 transition font-medium"
        >
          <Save className="w-4 h-4" />
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </CardContent>
    </Card>
  );
}
