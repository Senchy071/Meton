import axios, { AxiosInstance } from 'axios';

export class MetonClient {
    private client: AxiosInstance;
    private serverUrl: string;

    constructor(serverUrl: string) {
        this.serverUrl = serverUrl;
        this.client = axios.create({
            baseURL: serverUrl,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
    }

    async checkConnection(): Promise<boolean> {
        try {
            const response = await this.client.get('/health');
            return response.status === 200;
        } catch (error) {
            return false;
        }
    }

    async sendQuery(query: string): Promise<string> {
        const response = await this.client.post('/query', { query });
        return response.data.response;
    }

    async explainCode(code: string, language: string): Promise<string> {
        const query = `Explain this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\``;
        return this.sendQuery(query);
    }

    async reviewCode(code: string, language: string): Promise<string> {
        const query = `Review this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\``;
        return this.sendQuery(query);
    }

    async generateTests(code: string, language: string): Promise<string> {
        const query = `Generate tests for this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\``;
        return this.sendQuery(query);
    }

    async suggestRefactorings(code: string, language: string): Promise<string> {
        const query = `Suggest refactorings for this ${language} code:\n\`\`\`${language}\n${code}\n\`\`\``;
        return this.sendQuery(query);
    }

    async indexWorkspace(workspacePath: string): Promise<void> {
        await this.client.post('/index', { path: workspacePath });
    }

    async searchCode(query: string): Promise<any[]> {
        const response = await this.client.post('/search', { query });
        return response.data.results;
    }

    disconnect(): void {
        // Cleanup if needed
    }
}
