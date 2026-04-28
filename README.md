# The Guerrilla Guide to the Art Museum of Colonial Williamsburg

### *Analyzing Gender and Racial Representation in Local Artistic Spaces*

This project is a Streamlit-based data dashboard inspired by the activist-aesthetic of the **Guerrilla Girls**. It analyzes a hand-collected dataset from the Art Museum of Colonial Williamsburg to investigate latent trends in institutional underrepresentation.

---

## 📊 Overview
In 1989 (and again in 2004), the Guerrilla Girls famously asked, *"Do women have to be naked to get into the Met. Museum?"* This project brings that same critical lens to a local level. By analyzing both raw statistics and the descriptive language used in gallery plaques, this dashboard explores:
- **The Creator Gap:** The disparity between male and female artists in the collection.
- **The Subject/Author Divide:** How often women appear as subjects versus creators.
- **Racial Inclusion:** The representation of artists and figures of color.
- **Plaque Semantics:** Difference in language used to describe male vs. female figures.

## 🚀 Features
- **Museum Presentation Mode:** A looping, high-contrast carousel featuring interactive charts and KPIs.
- **Word Cloud Analysis:** Comparative text analysis of plaque descriptions for artists and subjects, broken down by gender.
- **Methodology Documentation:** A transparent look at the data collection process and the importance of local activism.

## 🛠️ Technical Stack
- **Python 3.x**
- **Streamlit:** Web framework for the dashboard interface.
- **Pandas:** Data manipulation and analysis.
- **Matplotlib:** Custom-styled data visualizations.
- **WordCloud:** Natural language processing and visualization.

## 📂 Data Collection
The data was collected manually at the Colonial Art Museum. Every painting, drawing, and etching in the gallery was recorded. 
- **Fields recorded:** Title, Artist Gender, Artist Race, Subject Gender, Subject Race, and full Plaque Descriptions.
- **Verification:** Artist identities were cross-referenced with museum online records and biographical databases.

## 💻 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/cwm-museum-dashboard.git](https://github.com/yourusername/cwm-museum-dashboard.git)
   cd cwm-museum-dashboard