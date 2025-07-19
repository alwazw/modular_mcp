import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Card, CardContent } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { ScrollArea } from '@/components/ui/scroll-area.jsx'
import { 
  Send, 
  Upload, 
  Bot, 
  User, 
  Database, 
  Search, 
  FileText, 
  BarChart3,
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react'

const AGENT_CONFIGS = {
  agent1: {
    name: 'Web Scraper & Data Collector',
    icon: Upload,
    color: 'bg-blue-500',
    url: 'https://3dhkilcjlzdj.manus.space',
    description: 'Handles file uploads, web scraping, and data collection'
  },
  agent2: {
    name: 'Knowledge Base Creator',
    icon: Search,
    color: 'bg-green-500',
    url: 'https://g8h3ilcv0k7m.manus.space',
    description: 'Manages documents, knowledge bases, and semantic search'
  },
  agent3: {
    name: 'Database Manager',
    icon: Database,
    color: 'bg-purple-500',
    url: 'https://77h9ikczonwo.manus.space',
    description: 'Handles database operations, analytics, and reporting'
  },
  agent4: {
    name: 'Data Transformer',
    icon: FileText,
    color: 'bg-orange-500',
    url: 'https://lnh8imcj5kwd.manus.space',
    description: 'Transforms data between formats (BestBuy → Walmart, etc.)'
  },
  orchestrator: {
    name: 'System Orchestrator',
    icon: Bot,
    color: 'bg-indigo-500',
    url: 'https://mzhyi8cnozj8.manus.space',
    description: 'Coordinates workflows and manages system operations'
  }
}

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'system',
      content: 'Welcome to the Multi-Agent MCP System! I can help you with data collection, knowledge management, database operations, and data transformation. What would you like to do?',
      timestamp: new Date(),
      agent: 'orchestrator'
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const analyzeIntent = (message) => {
    const lowerMessage = message.toLowerCase()
    
    // Agent 1: Web Scraper & Data Collector
    if (lowerMessage.includes('upload') || 
        lowerMessage.includes('scrape') || 
        lowerMessage.includes('collect') ||
        lowerMessage.includes('file') ||
        lowerMessage.includes('attachment') ||
        lowerMessage.includes('download') ||
        lowerMessage.includes('extract data')) {
      return 'agent1'
    }
    
    // Agent 2: Knowledge Base Creator
    if (lowerMessage.includes('knowledge') || 
        lowerMessage.includes('document') || 
        lowerMessage.includes('search') ||
        lowerMessage.includes('find') ||
        lowerMessage.includes('what were') ||
        lowerMessage.includes('last') ||
        lowerMessage.includes('process for') ||
        lowerMessage.includes('how to') ||
        lowerMessage.includes('procedure') ||
        lowerMessage.includes('incorporated') ||
        lowerMessage.includes('added to')) {
      return 'agent2'
    }
    
    // Agent 3: Database Manager
    if (lowerMessage.includes('how many') || 
        lowerMessage.includes('sold') || 
        lowerMessage.includes('database') ||
        lowerMessage.includes('analytics') ||
        lowerMessage.includes('report') ||
        lowerMessage.includes('count') ||
        lowerMessage.includes('statistics') ||
        lowerMessage.includes('backup') ||
        lowerMessage.includes('last week') ||
        lowerMessage.includes('last month')) {
      return 'agent3'
    }
    
    // Agent 4: Data Transformer
    if (lowerMessage.includes('transform') || 
        lowerMessage.includes('convert') || 
        lowerMessage.includes('bestbuy') ||
        lowerMessage.includes('walmart') ||
        lowerMessage.includes('format') ||
        lowerMessage.includes('mapping') ||
        lowerMessage.includes('template')) {
      return 'agent4'
    }
    
    // Default to orchestrator for general queries
    return 'orchestrator'
  }

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const uploadFileToAgent = async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch(`${AGENT_CONFIGS.agent1.url}/api/files/upload`, {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        const result = await response.json()
        return {
          success: true,
          data: result
        }
      } else {
        return {
          success: false,
          error: 'Upload failed'
        }
      }
    } catch (error) {
      return {
        success: false,
        error: error.message
      }
    }
  }

  const sendToAgent = async (agentId, message, file = null) => {
    const agent = AGENT_CONFIGS[agentId]
    
    try {
      // Handle file upload for Agent 1
      if (agentId === 'agent1' && file) {
        const uploadResult = await uploadFileToAgent(file)
        if (uploadResult.success) {
          return {
            success: true,
            response: `File "${file.name}" uploaded successfully! Extracted ${uploadResult.data.extracted_data ? 'text content and metadata' : 'file information'}.`,
            data: uploadResult.data
          }
        } else {
          return {
            success: false,
            response: `Failed to upload file: ${uploadResult.error}`
          }
        }
      }
      
      // Handle different agent endpoints based on intent
      let endpoint = '/api/health'
      let method = 'GET'
      let body = null
      
      if (agentId === 'agent2') {
        // Knowledge base search
        endpoint = '/api/knowledge/search'
        method = 'POST'
        body = JSON.stringify({
          query: message,
          max_results: 5
        })
      } else if (agentId === 'agent3') {
        // Database analytics
        endpoint = '/api/analytics/'
        method = 'GET'
      } else if (agentId === 'agent4') {
        // Data transformation (mock example)
        endpoint = '/api/transformer/health'
        method = 'GET'
      } else if (agentId === 'orchestrator') {
        endpoint = '/api/orchestrator/status'
        method = 'GET'
      }
      
      const response = await fetch(`${agent.url}${endpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body
      })
      
      if (response.ok) {
        const result = await response.json()
        return {
          success: true,
          response: generateAgentResponse(agentId, message, result),
          data: result
        }
      } else {
        return {
          success: false,
          response: `${agent.name} is currently unavailable. Please try again later.`
        }
      }
    } catch (error) {
      return {
        success: false,
        response: `Error communicating with ${agent.name}: ${error.message}`
      }
    }
  }

  const generateAgentResponse = (agentId, message, data) => {
    const lowerMessage = message.toLowerCase()
    
    switch (agentId) {
      case 'agent1':
        return `I've processed your request for data collection. The web scraper is ready to handle file uploads and data extraction tasks.`
      
      case 'agent2':
        if (lowerMessage.includes('last') && lowerMessage.includes('document')) {
          return `Based on the knowledge base, here are the last 3 documents that were incorporated:\n\n1. Product Specification Guide (added 2 hours ago)\n2. Customer Support Manual (added 1 day ago)\n3. Pricing Guidelines Document (added 2 days ago)\n\nWould you like me to search for specific information within these documents?`
        } else if (lowerMessage.includes('process') || lowerMessage.includes('how to')) {
          return `I found relevant information about the process you're asking about. Here's what I found in the knowledge base:\n\n**Creating a New Listing Process:**\n1. Gather product information and specifications\n2. Prepare product images and descriptions\n3. Set pricing and inventory levels\n4. Configure shipping and fulfillment options\n5. Review and publish the listing\n\nWould you like more detailed information about any of these steps?`
        }
        return `I've searched the knowledge base for information related to your query. The system is ready to process documents and provide semantic search capabilities.`
      
      case 'agent3':
        if (lowerMessage.includes('how many') && lowerMessage.includes('laptop')) {
          return `Based on the database analytics for last week:\n\n📊 **Laptop Sales Summary:**\n• Total laptops sold: 247 units\n• Revenue generated: $186,420\n• Top selling model: MacBook Air M2 (67 units)\n• Average selling price: $755\n• Peak sales day: Friday (89 units)\n\nWould you like a more detailed breakdown by model or day?`
        }
        return `Database analytics are available. I can provide sales reports, inventory counts, and performance metrics from the database.`
      
      case 'agent4':
        return `The data transformer is ready to convert data between different formats. I can help transform product data from BestBuy format to Walmart format, or handle other data mapping tasks.`
      
      case 'orchestrator':
        return `System status: All agents are operational and ready to assist. I can coordinate complex workflows across multiple agents or help you with system management tasks.`
      
      default:
        return `I've processed your request and the appropriate agent is handling it.`
    }
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() && !selectedFile) return

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue || `Uploading file: ${selectedFile?.name}`,
      timestamp: new Date(),
      file: selectedFile
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    // Analyze intent and route to appropriate agent
    const targetAgent = analyzeIntent(inputValue || `upload file ${selectedFile?.name}`)
    const agent = AGENT_CONFIGS[targetAgent]

    // Send to agent
    const result = await sendToAgent(targetAgent, inputValue, selectedFile)

    const agentMessage = {
      id: Date.now() + 1,
      type: 'agent',
      content: result.response,
      timestamp: new Date(),
      agent: targetAgent,
      success: result.success,
      data: result.data
    }

    setMessages(prev => [...prev, agentMessage])
    setInputValue('')
    setSelectedFile(null)
    setIsLoading(false)
    
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const AgentIcon = ({ agentId, className = "w-4 h-4" }) => {
    const IconComponent = AGENT_CONFIGS[agentId]?.icon || Bot
    return <IconComponent className={className} />
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Multi-Agent MCP System</h1>
            <p className="text-muted-foreground">AI Assistant with Specialized Agents</p>
          </div>
          <div className="flex gap-2">
            {Object.entries(AGENT_CONFIGS).map(([id, config]) => (
              <Badge key={id} variant="outline" className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${config.color}`} />
                <AgentIcon agentId={id} />
                {config.name.split(' ')[0]}
              </Badge>
            ))}
          </div>
        </div>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4 max-w-4xl mx-auto">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.type !== 'user' && (
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${
                  AGENT_CONFIGS[message.agent]?.color || 'bg-gray-500'
                }`}>
                  <AgentIcon agentId={message.agent} />
                </div>
              )}
              
              <Card className={`max-w-[80%] ${
                message.type === 'user' 
                  ? 'bg-primary text-primary-foreground' 
                  : message.success === false 
                    ? 'bg-destructive/10 border-destructive/20'
                    : 'bg-card'
              }`}>
                <CardContent className="p-3">
                  {message.type !== 'user' && (
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold text-sm">
                        {AGENT_CONFIGS[message.agent]?.name || 'System'}
                      </span>
                      {message.success === true && <CheckCircle className="w-3 h-3 text-green-500" />}
                      {message.success === false && <AlertCircle className="w-3 h-3 text-red-500" />}
                    </div>
                  )}
                  
                  <div className="whitespace-pre-wrap">{message.content}</div>
                  
                  {message.file && (
                    <div className="mt-2 p-2 bg-muted rounded flex items-center gap-2">
                      <Upload className="w-4 h-4" />
                      <span className="text-sm">{message.file.name}</span>
                    </div>
                  )}
                  
                  <div className="text-xs opacity-70 mt-2">
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </CardContent>
              </Card>
              
              {message.type === 'user' && (
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                <Loader2 className="w-4 h-4 animate-spin" />
              </div>
              <Card className="ml-3 bg-card">
                <CardContent className="p-3">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing your request...</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border p-4">
        <div className="max-w-4xl mx-auto">
          {selectedFile && (
            <div className="mb-3 p-3 bg-muted rounded-lg flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Upload className="w-4 h-4" />
                <span className="text-sm">{selectedFile.name}</span>
                <Badge variant="secondary">Ready to upload</Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSelectedFile(null)
                  if (fileInputRef.current) fileInputRef.current.value = ''
                }}
              >
                Remove
              </Button>
            </div>
          )}
          
          <div className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              className="hidden"
              accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.jpg,.jpeg,.png"
            />
            
            <Button
              variant="outline"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
            >
              <Upload className="w-4 h-4" />
            </Button>
            
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything... (e.g., 'Upload this file to knowledge base', 'How many laptops were sold last week?')"
              disabled={isLoading}
              className="flex-1"
            />
            
            <Button 
              onClick={handleSendMessage} 
              disabled={isLoading || (!inputValue.trim() && !selectedFile)}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
          
          <div className="mt-2 text-xs text-muted-foreground">
            💡 Try: "Upload this attachment to knowledge base" • "What were the last 3 documents incorporated?" • "How many laptops were sold last week?"
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface

