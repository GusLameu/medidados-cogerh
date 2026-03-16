import pandas as pd
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import numpy as np
import os
import processador
from config import MEDIDORES

# --- CONFIGURAÇÕES VISUAIS (PALETA DE ALTO CONTRASTE) ---
COR_VAZAO = '#0047AB'      # Azul Cobalto (Principal)
COR_VELOCIDADE = '#D32F2F' # Vermelho (Secundário/Alerta)
COR_TEXTO = '#333333'
CORES_ROSCA = ['#0047AB', '#FFC107', '#D32F2F', '#2E7D32'] # Sequência de cores para os gráficos circulares

class JanelaDashboard(ctk.CTkToplevel):
    """
    Janela secundária que renderiza o Dashboard após o processamento dos dados.
    """
    def __init__(self, parent, df, modelo):
        super().__init__(parent)
        self.parent = parent
        self.title(f"Medidados - Dashboard: {modelo}")
        
        # Configuração de Geometria: Inicia maximizado para melhor visualização
        largura, altura = 1400, 900
        x = (self.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.winfo_screenheight() // 2) - (altura // 2)
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.state('zoomed')
        self.configure(fg_color="white")
        
        # Carregamento do ícone com atraso para evitar conflitos de renderização no Windows
        try: self.after(200, lambda: self.iconbitmap("logo.ico"))
        except: pass

        self.protocol("WM_DELETE_WINDOW", self.ao_fechar)

        # Processamento das métricas via módulo externo (processador.py)
        faixas, qualidades, ind = processador.calcular_metricas_dashboard(df)

        # Configurações globais do Matplotlib para integração com o CustomTkinter
        plt.rcParams['axes.facecolor'] = '#ffffff'
        plt.rcParams['figure.facecolor'] = '#ffffff'
        plt.rcParams['font.sans-serif'] = ['Arial']
        plt.rcParams['text.color'] = COR_TEXTO
        
        self.fig = plt.figure(figsize=(16, 10), dpi=100)
        # GridSpec: Define o layout (2 linhas, 2 colunas). top=0.85 abre espaço para título/legenda.
        gs = self.fig.add_gridspec(2, 2, height_ratios=[1.5, 1], hspace=0.5, wspace=0.3, top=0.85, bottom=0.1)

        # --- 1. GRÁFICO DE SÉRIE TEMPORAL (EIXO DUPLO) ---
        self.ax1 = self.fig.add_subplot(gs[0, :]) # Ocupa a linha superior inteira
        self.ax2 = self.ax1.twinx()               # Cria eixo secundário para Velocidade

        # Formatador para o eixo Y: Transforma 1000 em 1k para não poluir visualmente
        def format_mil(x, pos):
            return f'{x/1000:,.1f}k'.replace('.', ',') if x >= 1000 else int(x)
        
        self.ax1.yaxis.set_major_formatter(FuncFormatter(format_mil))
        self.ax1.set_ylabel("Vazão (m³/h)", color=COR_VAZAO, fontsize=12, fontweight='bold')
        self.ax1.tick_params(axis='y', labelcolor=COR_VAZAO)
        
        self.ax2.set_ylabel("Velocidade (m/s)", color=COR_VELOCIDADE, fontsize=12, fontweight='bold')
        self.ax2.tick_params(axis='y', labelcolor=COR_VELOCIDADE)
        
        # Estilização das bordas (spines)
        self.ax2.spines['right'].set_color(COR_VELOCIDADE)
        self.ax2.spines['left'].set_color(COR_VAZAO)
        self.ax2.spines['top'].set_visible(False)

        # Formatação de datas no eixo X
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        self.ax1.set_xlim(df['Data'].min(), df['Data'].max())

        # Plotagem das Linhas
        self.line_vazao, = self.ax1.plot(df['Data'], df['Vazao'], label='VAZÃO', color=COR_VAZAO, lw=2.5)
        self.ax1.fill_between(df['Data'], df['Vazao'], color=COR_VAZAO, alpha=0.1) # Área preenchida sob a vazão
        self.line_vel, = self.ax2.plot(df['Data'], df['Velocidade'], label='VELOCIDADE', color=COR_VELOCIDADE, lw=2, linestyle='--')

        # Cursor Vertical de acompanhamento (zorder baixo para ficar atrás do balão de texto)
        self.v_line = self.ax1.axvline(x=df['Data'].iloc[0], color='#333333', linestyle='-', alpha=0.4, lw=1, zorder=5)
        self.v_line.set_visible(False)

        # Título e Legenda Superior
        self.ax1.set_title("MONITORAMENTO DE VAZÃO E VELOCIDADE", fontsize=18, fontweight='bold', pad=45)
        lines1, labels1 = self.ax1.get_legend_handles_labels()
        lines2, labels2 = self.ax2.get_legend_handles_labels()
        self.ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False)
        self.ax1.grid(True, axis='y', linestyle=':', alpha=0.4)

        # Balão de Tooltip (zorder=20 garante que fique sempre na frente de tudo)
        self.annot_line = self.ax1.annotate("", xy=(0,0), xytext=(15,15), textcoords="offset points",
                            bbox=dict(boxstyle="round4,pad=0.5", fc="white", ec=COR_VAZAO, lw=2, alpha=0.98),
                            arrowprops=dict(arrowstyle="->", color=COR_VAZAO), zorder=20)
        self.annot_line.set_visible(False)

        # --- 2. GRÁFICOS DE ROSCA (DISTRIBUIÇÃO) ---
        self.wedges_map = {} # Dicionário para mapear fatias do gráfico aos seus dados
        for i, (dados, titulo, pos) in enumerate([(faixas, "Percentual por faixa", (1,0)), 
                                                 (qualidades, "Qualidade dos dados", (1,1))]):
            ax = self.fig.add_subplot(gs[pos[0], pos[1]])
            valores, labels = list(dados.values()), list(dados.keys())
            
            # width=0.35 define o buraco interno (transforma pizza em rosca)
            wedges, _ = ax.pie(valores, startangle=90, colors=CORES_ROSCA, wedgeprops={'width': 0.35, 'edgecolor': 'white'})
            ax.set_title(titulo, fontsize=14, fontweight='bold', pad=20)
            
            # Armazena metadados para o evento de hover
            for w, label, val in zip(wedges, labels, valores):
                self.wedges_map[w] = {'label': label, 'valor': val, 'total': sum(valores)}

            # Rótulos externos com linhas de chamada (Callouts)
            kw = dict(arrowprops=dict(arrowstyle="-", color="#333333", lw=1.2), zorder=1, va="center")
            for j, p in enumerate(wedges):
                ang = (p.theta2 - p.theta1)/2. + p.theta1
                y, x = np.sin(np.deg2rad(ang)), np.cos(np.deg2rad(ang))
                horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
                pct = valores[j] / sum(valores) * 100
                ax.annotate(f"{pct:.1f}%", xy=(x, y), xytext=(1.35*np.sign(x), 1.4*y),
                            horizontalalignment=horizontalalignment, **kw, fontsize=11, fontweight='bold')

        # Tooltip para os gráficos de rosca
        self.annot_pie = self.fig.text(0, 0, "", bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="black", lw=1, alpha=0.98), 
                                      visible=False, zorder=20)

        # --- MONTAGEM DA INTERFACE ---
        self.container = ctk.CTkFrame(self, fg_color="white")
        self.container.pack(fill="both", expand=True, padx=20)

        # Canvas do Matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.container)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

        # Painel Lateral de Informações
        frame_lat = ctk.CTkFrame(self.container, width=320, fg_color="#f0f0f0", corner_radius=15)
        frame_lat.pack(side="right", fill="y", padx=10, pady=20)

        self.add_lbl(frame_lat, "Nº DE SÉRIE", ind['serie'])
        ctk.CTkLabel(frame_lat, text="PERÍODO", font=("Arial", 11, "bold"), text_color="#666666").pack(pady=(30, 0))
        ctk.CTkLabel(frame_lat, text=f"{ind['data_inicio'].strftime('%d/%m/%Y %H:%M')}\naté\n{ind['data_fim'].strftime('%d/%m/%Y %H:%M')}", 
                     font=("Arial", 12, "bold"), text_color="#000000").pack(pady=5)
        self.add_lbl(frame_lat, "TOTAL POSITIVO", f"{ind['total_positivo']:,.0f}".replace(',', '.'))

        # Botões de Ação
        ctk.CTkButton(frame_lat, text="Exportar Relatório", command=self.exportar, fg_color=COR_VAZAO, height=45).pack(pady=(50, 10), padx=30, fill="x")
        ctk.CTkButton(frame_lat, text="Nova Importação", command=self.ao_fechar, fg_color="#6c757d", height=45).pack(pady=10, padx=30, fill="x")

    def add_lbl(self, m, t, v):
        """Helper para adicionar rótulos formatados na sidebar."""
        ctk.CTkLabel(m, text=t, font=("Arial", 11, "bold"), text_color="#666666").pack(pady=(30,0))
        ctk.CTkLabel(m, text=str(v), font=("Arial", 22, "bold"), text_color="#000000").pack(pady=(0,5))

    def on_hover(self, event):
        """Lógica de interatividade: atualiza tooltips e cursor vertical ao mover o mouse."""
        # Se o mouse estiver sobre o gráfico de linhas
        if event.inaxes in [self.ax1, self.ax2] and event.xdata is not None:
            self.annot_pie.set_visible(False)
            x_data, y_vazao = self.line_vazao.get_data()
            _, y_vel = self.line_vel.get_data()
            x_num = mdates.date2num(x_data)
            idx = np.abs(x_num - event.xdata).argmin() # Encontra o ponto mais próximo no eixo X
            
            data_atual, val_vazao, val_vel = x_data[idx], y_vazao[idx], y_vel[idx]
            self.v_line.set_xdata([data_atual, data_atual])
            self.v_line.set_visible(True)
            
            data_f = pd.Timestamp(data_atual).strftime('%d/%m/%Y %H:%M')
            texto = (f"DATA: {data_f}\n"
                     f"VAZAO: {val_vazao:,.2f} m3/h\n"
                     f"VELOCIDADE: {val_vel:.2f} m/s")
            
            self.annot_line.xy = (data_atual, val_vazao)
            # Inverte o lado do balão dependendo da posição do mouse para não cortar na borda
            offset_x = -130 if event.xdata > np.mean(self.ax1.get_xlim()) else 20
            self.annot_line.set_position((offset_x, 0))
            self.annot_line.set_text(texto)
            self.annot_line.set_visible(True)
            self.canvas.draw_idle()

        # Se o mouse estiver sobre as roscas
        elif event.inaxes is not None and event.inaxes not in [self.ax1, self.ax2]:
            self.annot_line.set_visible(False)
            self.v_line.set_visible(False)
            found = False
            for wedge, info in self.wedges_map.items():
                if wedge.contains_point([event.x, event.y]):
                    pct = info['valor'] / info['total'] * 100
                    texto = f"CATEGORIA: {info['label']}\nQtd: {info['valor']}\nPct: {pct:.1f}%"
                    self.annot_pie.set_text(texto)
                    # Converte coordenadas de pixels para coordenadas da figura (0 a 1)
                    self.annot_pie.set_position((event.x/self.fig.bbox.width + 0.02, event.y/self.fig.bbox.height + 0.02))
                    self.annot_pie.set_visible(True)
                    found = True
                    break
            if not found: self.annot_pie.set_visible(False)
            self.canvas.draw_idle()
        else:
            # Oculta tudo se o mouse sair das áreas de interesse
            self.annot_line.set_visible(False)
            self.annot_pie.set_visible(False)
            self.v_line.set_visible(False)
            self.canvas.draw_idle()

    def ao_fechar(self):
        self.parent.deiconify() # Mostra a janela inicial novamente
        self.destroy()

    def exportar(self):
        """Salva o dashboard atual como imagem PNG de alta resolução."""
        path = filedialog.asksaveasfilename(defaultextension=".png", 
                                            filetypes=[("Imagem PNG", "*.png")])
        if path: self.fig.savefig(path, dpi=300, bbox_inches='tight')

# --- JANELA DE ENTRADA (MÓDULO DE IMPORTAÇÃO) ---
class AppAnalise(ctk.CTk, TkinterDnD.DnDWrapper):
    """
    Janela Principal: Gerencia a seleção do modelo e a importação do arquivo.
    """
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self) # Inicializa suporte a Arrastar e Soltar
        
        self.title("Medidados")
        l, a = 600, 750
        x, y = (self.winfo_screenwidth()//2 - l//2), (self.winfo_screenheight()//2 - a//2)
        self.geometry(f"{l}x{a}+{x}+{y}")
        self.configure(fg_color="white")
        
        try: self.iconbitmap("logo.ico")
        except: pass

        # Registra a janela inteira como destino de arquivos arrastados
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.soltar_arquivo)

        # Branding
        ctk.CTkLabel(self, text="Medidados", font=("Arial", 32, "bold"), text_color=COR_VAZAO).pack(pady=(50, 5))
        ctk.CTkLabel(self, text="Sistema de Análise Técnica", font=("Arial", 14), text_color="gray").pack(pady=(0, 40))

        # Seletores de Configuração
        self.cb_tipo = ctk.CTkComboBox(self, values=list(MEDIDORES.keys()), command=self.upd, state="readonly", width=380, height=45)
        self.cb_tipo.pack(pady=10); self.cb_tipo.set("1. Selecione o Tipo de Medidor...")

        self.cb_mod = ctk.CTkComboBox(self, values=[], state="disabled", width=380, height=45)
        self.cb_mod.pack(pady=10); self.cb_mod.set("2. Selecione o Modelo...")

        # Botão Manual
        ctk.CTkButton(self, text="BUSCAR ARQUIVO MANUALMENTE", command=self.run_manual, 
                      height=55, width=380, font=("Arial", 14, "bold"), fg_color=COR_VAZAO).pack(pady=30)

        ctk.CTkLabel(self, text="OU", font=("Arial", 11, "bold"), text_color="gray").pack(pady=10)

        # Drop Zone (Área Visual para Arrastar)
        self.frame_drop = ctk.CTkFrame(self, width=450, height=160, fg_color="#F0F8FF", border_width=2, border_color=COR_VAZAO, corner_radius=20)
        self.frame_drop.pack(pady=10); self.frame_drop.pack_propagate(False)
        ctk.CTkLabel(self.frame_drop, text="ARRASTE O ARQUIVO AQUI\n(Excel ou CSV)", font=("Arial", 15, "bold"), text_color=COR_VAZAO).pack(expand=True)

        ctk.CTkLabel(self, text="v1.0 | Medidados\nGustavo Lopes Lameu\nGEMED", font=("Arial", 10), text_color="gray").pack(side="bottom", pady=15)
        

    def upd(self, v):
        """Atualiza o segundo dropdown baseado na escolha do primeiro."""
        self.cb_mod.configure(state="readonly", values=MEDIDORES[v])
        self.cb_mod.set("2. Selecione o Modelo...")

    def soltar_arquivo(self, event):
        """Captura o caminho do arquivo quando ele é solto na janela."""
        filepath = event.data.strip('{}') # Remove chaves que o Windows adiciona em nomes com espaços
        self.processar_caminho(filepath)

    def run_manual(self):
        """Abre o seletor de arquivos padrão do sistema."""
        p = filedialog.askopenfilename(filetypes=[("Arquivos de Dados", "*.csv *.xlsx *.xls")])
        if p: self.processar_caminho(p)

    def processar_caminho(self, path):
        """Verifica se o modelo foi selecionado e inicia o processamento dos dados."""
        m = self.cb_mod.get()
        if "Selecione" in m:
            messagebox.showwarning("Atenção", "Selecione o TIPO e o MODELO do medidor antes de carregar o arquivo.")
            return
        try:
            df = processador.carregar_dados(path, m)
            self.withdraw() # Oculta a janela de importação
            JanelaDashboard(self, df, m)
        except Exception as e:
            messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo:\n{str(e)}")