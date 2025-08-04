# 🌱 App de Análise Agrometeorológica - Upload Excel

## 📋 Instruções Simplificadas

### ✨ **Novidades desta versão:**
- ✅ **Upload direto de Excel** (.xlsx/.xls) - sem Google Sheets API
- ✅ **Detecção automática** de colunas de temperatura e folhas
- ✅ **IA integrada** para análise automática dos resultados
- ✅ **Gráficos de dispersão** como na planilha modelo
- ✅ **Análise de múltiplas épocas/cultivares** automaticamente
- ✅ **Interface mais simples** e intuitiva

---

## 🚀 **Como usar no Replit/Streamlit Cloud:**

### 1. **Substitua os arquivos no seu projeto**
- Substitua `app_agrometeorologia.py` por `app_agrometeorologia_excel.py`
- Substitua `requirements.txt` por `requirements_excel.txt`

### 2. **No Replit:**
```bash
streamlit run app_agrometeorologia_excel.py --server.port 8080 --server.address 0.0.0.0
```

### 3. **No Streamlit Cloud:**
- Faça upload dos novos arquivos no GitHub
- O deploy será automático

---

## 📊 **Como preparar sua planilha Excel:**

### **Estrutura necessária:**
- **Formato:** `.xlsx` ou `.xls`
- **Colunas obrigatórias:**
  - Temperatura Mínima (ex: "Tmin", "T min", "Temp Min")
  - Temperatura Máxima (ex: "Tmax", "T max", "Temp Max") 
  - Número de Folhas (ex: "NF", "Folhas", "Número de Folhas")

### **Exemplo de estrutura:**
| Data | Tmin | Tmax | NF |
|------|------|------|----|
| 01/03 | 18.5 | 28.2 | 2 |
| 02/03 | 19.1 | 29.0 | 3 |
| 03/03 | 17.8 | 27.5 | 4 |

---

## 🤖 **Recursos com IA Integrada:**

### **Detecção Automática:**
- O app detecta automaticamente as colunas de temperatura e folhas
- Não precisa configurar manualmente (mas pode se quiser)

### **Análise Inteligente:**
- **Interpretação automática** do R² (excelente, bom, moderado, fraco)
- **Análise da Tb** (baixa, moderada, alta) com interpretação biológica
- **Avaliação do desenvolvimento** (rápido, moderado, lento)
- **Sugestões práticas** baseadas nos resultados

### **Visualizações:**
- **Gráfico R² vs Tb** com destaque do ponto ótimo
- **Gráfico de dispersão STa vs NF** (igual à planilha modelo)
- **Tabelas detalhadas** com todos os cálculos

---

## 📈 **Fluxo de Uso:**

1. **Upload** da planilha Excel
2. **Seleção** da aba (se houver múltiplas)
3. **Detecção automática** das colunas (ou seleção manual)
4. **Configuração** dos parâmetros (Tb min/max, passo)
5. **Execução** da análise automática
6. **Visualização** dos resultados com IA
7. **Download** dos dados processados

---

## 🎯 **Vantagens desta versão:**

- **Sem configuração de API** - muito mais simples
- **Upload direto** - sem dependência de Google Sheets
- **IA integrada** - análise automática e interpretação
- **Detecção inteligente** - encontra as colunas automaticamente
- **Gráficos profissionais** - igual à planilha modelo
- **Múltiplas épocas** - analisa diferentes cultivares/épocas
- **Download fácil** - exporta todos os resultados

---

## ⚠️ **Dicas importantes:**

- **Dados limpos:** Certifique-se de que as colunas de temperatura e NF contêm apenas números
- **Sem células vazias:** Evite células vazias nas colunas principais
- **Nomes das colunas:** Use nomes descritivos (Tmin, Tmax, NF, etc.)
- **Formato Excel:** Prefira .xlsx para melhor compatibilidade

---

**🎉 Agora é só fazer upload da sua planilha e deixar a IA fazer o resto!**
